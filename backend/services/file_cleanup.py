"""Automatic file cleanup service."""
import os
import time
import threading
from datetime import datetime, timedelta


class FileCleanupService:
    """Service for periodically cleaning up uploaded files."""
    
    def __init__(self, upload_folder: str, max_age_minutes: int = 30, check_interval_minutes: int = 5) -> None:
        """
        Initialize cleanup service.
        
        Args:
            upload_folder: Upload folder path
            max_age_minutes: Maximum file retention time in minutes
            check_interval_minutes: Check interval in minutes
        """
        self.upload_folder = upload_folder
        self.max_age_minutes = max_age_minutes
        self.check_interval_seconds = check_interval_minutes * 60
        self.is_running = False
        self.cleanup_thread = None
    
    def start(self) -> None:
        """Start the cleanup service."""
        if self.is_running:
            print("File cleanup service is already running")
            return
        
        self.is_running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        print(f"File cleanup service started:")
        print(f"  - Folder: {self.upload_folder}")
        print(f"  - Max file age: {self.max_age_minutes} minutes")
        print(f"  - Check interval: {self.check_interval_seconds // 60} minutes")
    
    def stop(self) -> None:
        """Stop the cleanup service."""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        print("File cleanup service stopped")
    
    def _cleanup_loop(self) -> None:
        """Cleanup loop running in background thread."""
        while self.is_running:
            try:
                self._cleanup_old_files()
            except Exception as e:
                print(f"Error during file cleanup: {str(e)}")
            
            # Wait for next check
            time.sleep(self.check_interval_seconds)
    
    def _cleanup_old_files(self) -> None:
        """Clean up expired files."""
        if not os.path.exists(self.upload_folder):
            return
        
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=self.max_age_minutes)
        
        deleted_count = 0
        total_size = 0
        
        for filename in os.listdir(self.upload_folder):
            # Skip special files
            if filename in ['.gitkeep', '.gitignore']:
                continue
            
            file_path = os.path.join(self.upload_folder, filename)
            
            # Only process files, skip directories
            if not os.path.isfile(file_path):
                continue
            
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Delete if file exceeds maximum retention time
                if file_mtime < cutoff_time:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_count += 1
                    total_size += file_size
                    
                    file_age_minutes = (now - file_mtime).total_seconds() / 60
                    print(f"[Cleanup] Deleted: {filename} (age: {file_age_minutes:.1f} min, size: {file_size / 1024:.2f} KB)")
            
            except PermissionError:
                print(f"[Cleanup] Permission denied: {filename} (file may be in use)")
            except Exception as e:
                print(f"[Cleanup] Failed to delete {filename}: {str(e)}")
        
        if deleted_count > 0:
            print(f"[Cleanup] Summary: {deleted_count} file(s) deleted, {total_size / 1024:.2f} KB freed")
        else:
            print(f"[Cleanup] No files to delete (checked {len(os.listdir(self.upload_folder))} items)")
    
    def cleanup_now(self) -> None:
        """Execute cleanup immediately (manual trigger)."""
        print("Manual cleanup triggered")
        self._cleanup_old_files()


# Global cleanup service instance
cleanup_service = None


def start_cleanup_service(upload_folder: str, max_age_minutes: int = 30, check_interval_minutes: int = 5):
    """
    Start file cleanup service.
    
    Args:
        upload_folder: Upload folder path
        max_age_minutes: Maximum file retention time in minutes
        check_interval_minutes: Check interval in minutes
    
    Returns:
        FileCleanupService instance
    """
    global cleanup_service
    
    if cleanup_service is None:
        cleanup_service = FileCleanupService(
            upload_folder,
            max_age_minutes,
            check_interval_minutes
        )
        cleanup_service.start()
    
    return cleanup_service


def stop_cleanup_service() -> None:
    """Stop file cleanup service."""
    global cleanup_service
    
    if cleanup_service:
        cleanup_service.stop()
        cleanup_service = None

