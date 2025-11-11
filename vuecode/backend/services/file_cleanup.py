"""文件自动清理服务"""
import os
import time
import threading
from datetime import datetime, timedelta


class FileCleanupService:
    """定时清理上传文件的服务"""
    
    def __init__(self, upload_folder, max_age_minutes=30, check_interval_minutes=5):
        """
        初始化清理服务
        
        Args:
            upload_folder: 上传文件夹路径
            max_age_minutes: 文件最大保留时间（分钟）
            check_interval_minutes: 检查间隔（分钟）
        """
        self.upload_folder = upload_folder
        self.max_age_minutes = max_age_minutes
        self.check_interval_seconds = check_interval_minutes * 60
        self.is_running = False
        self.cleanup_thread = None
    
    def start(self):
        """启动清理服务"""
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
    
    def stop(self):
        """停止清理服务"""
        self.is_running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        print("File cleanup service stopped")
    
    def _cleanup_loop(self):
        """清理循环"""
        while self.is_running:
            try:
                self._cleanup_old_files()
            except Exception as e:
                print(f"Error during file cleanup: {str(e)}")
            
            # 等待下一次检查
            time.sleep(self.check_interval_seconds)
    
    def _cleanup_old_files(self):
        """清理过期文件"""
        if not os.path.exists(self.upload_folder):
            return
        
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=self.max_age_minutes)
        
        deleted_count = 0
        total_size = 0
        
        for filename in os.listdir(self.upload_folder):
            # 跳过特殊文件
            if filename in ['.gitkeep', '.gitignore']:
                continue
            
            file_path = os.path.join(self.upload_folder, filename)
            
            # 只处理文件，跳过文件夹
            if not os.path.isfile(file_path):
                continue
            
            try:
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # 如果文件超过最大保留时间，删除
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
    
    def cleanup_now(self):
        """立即执行清理（手动触发）"""
        print("Manual cleanup triggered")
        self._cleanup_old_files()


# 全局清理服务实例
cleanup_service = None


def start_cleanup_service(upload_folder, max_age_minutes=30, check_interval_minutes=5):
    """启动文件清理服务"""
    global cleanup_service
    
    if cleanup_service is None:
        cleanup_service = FileCleanupService(
            upload_folder,
            max_age_minutes,
            check_interval_minutes
        )
        cleanup_service.start()
    
    return cleanup_service


def stop_cleanup_service():
    """停止文件清理服务"""
    global cleanup_service
    
    if cleanup_service:
        cleanup_service.stop()
        cleanup_service = None

