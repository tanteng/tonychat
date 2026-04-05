import os
import json
from flask import Blueprint, request, jsonify, Response, render_template
from werkzeug.utils import secure_filename

from application.services.document_service import get_document_service
from application.services.chat_service import get_chat_service
from infrastructure.persistence.database import get_database


# Create blueprint
api_bp = Blueprint('api', __name__)

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt', 'md', 'pdf', 'docx'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_filename(filename):
    """Sanitize filename but preserve Chinese and Unicode characters"""
    # Get name and extension
    if '.' in filename:
        name, ext = filename.rsplit('.', 1)
        ext = ext.lower()
    else:
        name = filename
        ext = ''

    # Keep Unicode characters (Chinese, etc.), only remove dangerous chars
    # Remove path separators and null bytes
    safe_name = name.replace('/', '').replace('\\', '').replace('\x00', '')
    safe_name = safe_name.strip()

    if ext:
        return f"{safe_name}.{ext}"
    return safe_name


@api_bp.route('/')
def index():
    """Serve the chat interface"""
    return render_template('index.html')


@api_bp.route('/upload', methods=['POST'])
def upload_files():
    """Upload files - returns immediately after save"""
    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    uploaded = []

    for file in files:
        if file.filename == '':
            continue

        if file and allowed_file(file.filename):
            filename = sanitize_filename(file.filename)
            filepath = os.path.join('uploads', filename)

            # Handle duplicate filenames
            if os.path.exists(filepath):
                name, ext = filename.rsplit('.', 1)
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{name}_{counter}.{ext}"
                    filepath = os.path.join('uploads', filename)
                    counter += 1

            file.save(filepath)
            uploaded.append(filename)

    return jsonify({'success': True, 'files': uploaded})


@api_bp.route('/process', methods=['POST'])
def process_files():
    """Process uploaded files with SSE progress streaming (parsing + vectorizing)"""
    data = request.get_json()
    filenames = data.get('files', [])

    if not filenames:
        return jsonify({'success': False, 'error': 'No files provided'}), 400

    def generate_sse():
        for filename in filenames:
            try:
                # Load and split with progress
                yield f"event: progress\ndata: {json.dumps({'filename': filename, 'stage': 'parsing', 'progress': 30})}\n\n"

                from infrastructure.document_loading.document_loader import DocumentLoader
                loader = DocumentLoader()

                filepath = os.path.join('uploads', filename)
                docs = loader.load_file(filepath)

                yield f"event: progress\ndata: {json.dumps({'filename': filename, 'stage': 'splitting', 'progress': 50})}\n\n"

                # Vectorize with progress
                if docs:
                    from infrastructure.vectorstore.faiss_store import get_vector_store
                    from infrastructure.embeddings.openai_embeddings import get_embeddings_adapter
                    from langchain_community.vectorstores import FAISS

                    vector_store = get_vector_store()
                    embeddings = get_embeddings_adapter()

                    total = len(docs)
                    batch_size = 10

                    for i in range(0, total, batch_size):
                        batch = docs[i:i+batch_size]
                        if vector_store.store is None:
                            if i == 0:
                                vector_store._store = FAISS.from_documents(batch, embeddings.embeddings)
                            else:
                                vector_store.add_documents(batch, embeddings.embeddings)
                        else:
                            vector_store.add_documents(batch, embeddings.embeddings)

                        pct = min(90, 50 + int((i + len(batch)) / total * 40))
                        yield f"event: progress\ndata: {json.dumps({'filename': filename, 'stage': 'vectorizing', 'progress': pct})}\n\n"

                    vector_store.save()

                yield f"event: progress\ndata: {json.dumps({'filename': filename, 'stage': 'complete', 'progress': 100})}\n\n"

            except Exception as e:
                import traceback
                traceback.print_exc()
                yield f"event: error\ndata: {json.dumps({'filename': filename, 'error': str(e)})}\n\n"

        yield f"event: done\ndata: {json.dumps({'success': True})}\n\n"

    return Response(
        generate_sse(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@api_bp.route('/files', methods=['GET'])
def list_files():
    """List uploaded files"""
    document_service = get_document_service()
    documents = document_service.get_all_documents()

    files = [
        {
            'id': doc.id,
            'filename': doc.filename,
            'file_type': doc.file_type,
            'uploaded_at': doc.uploaded_at.isoformat(),
            'chunk_count': doc.chunk_count
        }
        for doc in documents
    ]

    return jsonify({'files': files})


@api_bp.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    filename = sanitize_filename(filename)
    document_service = get_document_service()

    try:
        document_service.delete_document(filename)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404


import uuid


@api_bp.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint with RAG and conversation history - AG-UI streaming protocol"""
    data = request.get_json()
    message = data.get('message', '')
    model = data.get('model', 'openai')
    session_id = data.get('session_id', 'default')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    chat_service = get_chat_service()

    def generate():
        message_id = str(uuid.uuid4())
        try:
            # Send TextMessageStart event
            yield f"event: text_message_start\ndata: {json.dumps({'messageId': message_id, 'role': 'assistant'})}\n\n"

            full_content = ""
            # Use sync streaming method (simulated streaming by chunking the response)
            for chunk in chat_service.chat_stream(message, session_id=session_id):
                full_content += chunk
                # Send TextMessageContent event (AG-UI format)
                yield f"event: text_message_content\ndata: {json.dumps({'messageId': message_id, 'delta': chunk})}\n\n"

            # Send TextMessageEnd event
            yield f"event: text_message_end\ndata: {json.dumps({'messageId': message_id})}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            # Send error event
            yield f"event: text_message_end\ndata: {json.dumps({'messageId': message_id, 'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@api_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """获取会话列表"""
    db = get_database()
    sessions = db.get_all_sessions()
    return jsonify({
        'sessions': [
            {
                'id': s.id,
                'title': s.title,
                'created_at': s.created_at.isoformat(),
                'updated_at': s.updated_at.isoformat()
            }
            for s in sessions
        ]
    })


@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """创建新会话"""
    db = get_database()
    session = db.create_session()
    return jsonify({
        'session': {
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        }
    }), 201


@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    db = get_database()
    try:
        db.delete_session(session_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404


@api_bp.route('/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """获取会话的历史消息"""
    db = get_database()
    try:
        messages = db.get_conversation_history(session_id, limit=50)
        return jsonify({
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in messages
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 404
