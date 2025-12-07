import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException, status


# Storage configuration
STORAGE_DIR = Path("storage/documents")
TEMP_DIR = Path("storage/temp")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Allowed file types and their possible MIME types
ALLOWED_EXTENSIONS = {
    "pdf": ["application/pdf"],
    "docx": [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
        "application/zip",
        "application/x-zip-compressed",
        "application/msword"  # Sometimes misclassified
    ],
    "doc": [
        "application/msword",
        "application/vnd.ms-word",
        "application/octet-stream"  # Fallback for older formats
    ],
    "txt": ["text/plain"],
}

# Flatten all allowed MIME types
ALLOWED_MIME_TYPES = set()
for mime_types in ALLOWED_EXTENSIONS.values():
    ALLOWED_MIME_TYPES.update(mime_types)


def ensure_storage_dirs():
    """Create storage directories if they don't exist"""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename"""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_file_type(file: UploadFile) -> None:
    """
    Validate uploaded file type.
    
    Args:
        file: Uploaded file
        
    Raises:
        HTTPException: If file type is not allowed
    """
    # Check by extension first
    extension = get_file_extension(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{extension}' not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    
    # Check if MIME type matches the extension's allowed types
    allowed_mimes_for_ext = ALLOWED_EXTENSIONS[extension]
    if file.content_type not in allowed_mimes_for_ext:
        # Allow if it's in the general allowed list (for generic types like octet-stream)
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MIME type '{file.content_type}' for .{extension}. Expected one of: {', '.join(allowed_mimes_for_ext)}"
            )


def validate_file_size(file_size: int) -> None:
    """
    Validate file size.
    
    Args:
        file_size: Size in bytes
        
    Raises:
        HTTPException: If file is too large
    """
    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {max_mb}MB"
        )


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename while preserving extension.
    
    Args:
        original_filename: Original uploaded filename
        
    Returns:
        Unique filename with UUID prefix
    """
    extension = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex
    return f"{unique_id}.{extension}"


def get_file_path(stored_filename: str) -> Path:
    """
    Get full path to stored file.
    
    Args:
        stored_filename: Unique filename in storage
        
    Returns:
        Full path to file
    """
    return STORAGE_DIR / stored_filename


async def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
    """
    Save uploaded file to storage.
    
    Args:
        file: Uploaded file
        
    Returns:
        Tuple of (stored_filename, file_path, file_size)
        
    Raises:
        HTTPException: If validation fails or save fails
    """
    # Ensure storage directories exist
    ensure_storage_dirs()
    
    # Validate file type
    validate_file_type(file)
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    validate_file_size(file_size)
    
    # Generate unique filename
    stored_filename = generate_unique_filename(file.filename)
    file_path = get_file_path(stored_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    return stored_filename, str(file_path), file_size


def delete_file(stored_filename: str) -> bool:
    """
    Delete a file from storage.
    
    Args:
        stored_filename: Unique filename in storage
        
    Returns:
        True if deleted, False if file not found
    """
    file_path = get_file_path(stored_filename)
    
    if file_path.exists():
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
    
    return False


def file_exists(stored_filename: str) -> bool:
    """Check if file exists in storage"""
    return get_file_path(stored_filename).exists()