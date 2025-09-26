# 📄 Document Uploader with Zoning AI Processing

A web application that uploads zoning documents locally and automatically sends them to the Zoning AI backend for Grok LLM processing. Documents are analyzed to extract structured zoning data and saved to the Supabase database for searching.

## 🚀 Features

- **AI-Powered Processing**: Automatic zoning document analysis with Grok LLM
- **Database Integration**: Extracted zoning data saved to Supabase database
- **Dual Storage**: Files stored locally AND processed for zoning data
- **Municipality Tagging**: Optional municipality and state metadata
- **Simple Web Interface**: Clean, intuitive drag-and-drop upload interface
- **File Management**: Upload, download, and delete documents
- **File Type Support**: PDF, DOC, DOCX, TXT, JPG, PNG, TIFF, ZIP
- **Size Limits**: 50MB maximum file size
- **Real-time Updates**: Instant feedback and file listing
- **Mobile Friendly**: Responsive design works on all devices

## 🛠️ Quick Start

### Using Docker Compose (Recommended)

1. **Navigate to the directory:**
   ```bash
   cd document-uploader
   ```

2. **Start the application:**
   ```bash
   docker-compose up -d
   ```

3. **Access the web interface:**
   Open http://localhost:5001 in your browser

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Manual Docker Build

```bash
# Build the image
docker build -t document-uploader .

# Run the container
docker run -d \
  --name document-uploader \
  -p 5001:5000 \
  -v uploads_data:/app/uploads \
  document-uploader
```

## 📁 File Management

### Upload Files
- **Drag & Drop**: Simply drag files onto the upload area
- **Click to Browse**: Click the upload area to open file browser
- **Multiple Files**: Upload multiple files at once
- **Auto-rename**: Files get unique names to prevent conflicts

### Manage Files
- **Download**: Click "Download" to save files to your computer
- **Delete**: Click "Delete" to remove files (with confirmation)
- **View Details**: See file size, type, and modification date
- **Statistics**: View total files and storage usage

## 🔧 Configuration

### Supported File Types
- **Documents**: PDF, DOC, DOCX, TXT
- **Images**: JPG, JPEG, PNG, TIFF
- **Archives**: ZIP

### File Size Limits
- **Maximum**: 50MB per file
- **Storage**: Persistent Docker volume

## 🔄 Processing Workflow

1. **Upload Document**: User uploads zoning document via web interface
2. **Local Storage**: Document is saved locally in Docker volume
3. **AI Processing**: Document is automatically sent to Zoning AI backend
4. **Grok LLM Analysis**: Grok AI extracts zoning data (building codes, setbacks, density, etc.)
5. **Database Storage**: Structured zoning data saved to Supabase database
6. **Search Ready**: Data becomes searchable in the zoning frontend

## 🌐 API Endpoints

- `GET /` - Main web interface
- `POST /upload` - File upload and zoning processing endpoint
- `GET /download/<filename>` - Download file
- `POST /delete/<filename>` - Delete file
- `GET /api/files` - JSON API for file listing
- `GET /health` - Health check

## 📊 Usage Examples

### Upload a PDF
```bash
curl -X POST -F "file=@document.pdf" http://localhost:5001/upload
```

### List Files (JSON)
```bash
curl http://localhost:5001/api/files
```

### Download a File
```bash
curl -O http://localhost:5001/download/document.pdf
```

## 🔒 Security Features

- **Local Only**: Runs completely offline
- **File Validation**: Strict file type checking
- **Size Limits**: Prevents abuse with size restrictions
- **Secure Names**: Files renamed with UUIDs
- **Isolated Storage**: Docker volume isolation

## 🗂️ Data Persistence

Files are stored in a Docker named volume (`uploads_data`) and persist between container restarts. To backup your files:

```bash
# Copy files from container
docker cp document-uploader:/app/uploads ./backup/

# Or backup the volume
docker run --rm -v uploads_data:/source -v $(pwd):/backup alpine tar czf /backup/uploads.tar.gz -C /source .
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs document-uploader

# Check container status
docker-compose ps
```

### Files Not Appearing
```bash
# Check volume contents
docker-compose exec document-uploader ls -la /app/uploads/

# Check permissions
docker-compose exec document-uploader ls -ld /app/uploads/
```

### Port Already in Use
```bash
# Change port in docker-compose.yml
ports:
  - "5002:5000"  # Use different host port
```

## 🛠️ Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
# Access at http://localhost:5000
```

### Project Structure
```
document-uploader/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker build configuration
├── docker-compose.yml # Docker Compose setup
├── templates/
│   └── index.html     # Web interface template
└── README.md          # This file
```

## 📈 Future Enhancements

- [ ] User authentication
- [ ] File preview/thumbnails
- [ ] Bulk operations
- [ ] File search/filtering
- [ ] Upload progress bars
- [ ] File compression
- [ ] Cloud storage integration

## 🤝 Contributing

This is a standalone utility for local document management. For zoning analysis features, see the main Zoning Project repository.

## 📄 License

MIT License - Free to use for personal and commercial projects.
