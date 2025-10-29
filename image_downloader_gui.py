import csv
import os
import requests
from pathlib import Path
from urllib.parse import urlparse
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import zipfile
import shutil

class ImageDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Image Downloader")
        self.root.geometry("700x650")
        self.root.resizable(False, False)
        
        # Variables
        self.csv_file = tk.StringVar()
        self.output_folder = tk.StringVar(value="downloaded_images")
        self.compress_folders = tk.BooleanVar(value=True)  # Checked by default
        self.delete_after_zip = tk.BooleanVar(value=True)  # Delete folders after zipping
        self.is_downloading = False
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📥 CSV Image Downloader",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Main content frame
        content_frame = tk.Frame(self.root, padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # CSV File Selection
        csv_frame = tk.LabelFrame(content_frame, text="1. Select CSV File", font=("Arial", 10, "bold"), padx=10, pady=10)
        csv_frame.pack(fill=tk.X, pady=(0, 15))
        
        csv_entry_frame = tk.Frame(csv_frame)
        csv_entry_frame.pack(fill=tk.X)
        
        self.csv_entry = tk.Entry(csv_entry_frame, textvariable=self.csv_file, font=("Arial", 10), state="readonly")
        self.csv_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(
            csv_entry_frame,
            text="Browse",
            command=self.browse_csv,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # Output Folder Selection
        output_frame = tk.LabelFrame(content_frame, text="2. Select Output Folder", font=("Arial", 10, "bold"), padx=10, pady=10)
        output_frame.pack(fill=tk.X, pady=(0, 15))
        
        output_entry_frame = tk.Frame(output_frame)
        output_entry_frame.pack(fill=tk.X)
        
        self.output_entry = tk.Entry(output_entry_frame, textvariable=self.output_folder, font=("Arial", 10))
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        output_browse_btn = tk.Button(
            output_entry_frame,
            text="Browse",
            command=self.browse_output,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=20
        )
        output_browse_btn.pack(side=tk.RIGHT)
        
        # Options Frame
        options_frame = tk.LabelFrame(content_frame, text="3. Options", font=("Arial", 10, "bold"), padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Compress checkbox
        compress_check = tk.Checkbutton(
            options_frame,
            text="🗜️ Compress folders to ZIP files after download",
            variable=self.compress_folders,
            font=("Arial", 10),
            cursor="hand2",
            command=self.toggle_delete_option
        )
        compress_check.pack(anchor=tk.W, pady=(0, 5))
        
        # Delete after zip checkbox (indented)
        self.delete_check = tk.Checkbutton(
            options_frame,
            text="🗑️ Delete original folders after creating ZIP",
            variable=self.delete_after_zip,
            font=("Arial", 9),
            cursor="hand2"
        )
        self.delete_check.pack(anchor=tk.W, padx=(20, 0))
        
        # Download Button
        self.download_btn = tk.Button(
            content_frame,
            text="⬇ Start Download",
            command=self.start_download,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            cursor="hand2",
            height=2
        )
        self.download_btn.pack(fill=tk.X, pady=(0, 15))
        
        # Progress Bar
        self.progress = ttk.Progressbar(content_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 15))
        
        # Log Frame
        log_frame = tk.LabelFrame(content_frame, text="Download Log", font=("Arial", 10, "bold"), padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=12,
            font=("Consolas", 9),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_label = tk.Label(
            self.root,
            text="Ready to download",
            bg="#ecf0f1",
            anchor=tk.W,
            padx=10,
            font=("Arial", 9)
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def toggle_delete_option(self):
        """Enable/disable delete option based on compress checkbox"""
        if self.compress_folders.get():
            self.delete_check.config(state=tk.NORMAL)
        else:
            self.delete_check.config(state=tk.DISABLED)
    
    def browse_csv(self):
        filename = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            self.csv_file.set(filename)
            self.log(f"Selected CSV: {filename}")
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)
            self.log(f"Output folder: {folder}")
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def compress_folder_to_zip(self, folder_path, zip_path):
        """Compress a folder to a ZIP file"""
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            self.log(f"  ✗ Failed to compress: {str(e)}")
            return False
    
    def start_download(self):
        if not self.csv_file.get():
            messagebox.showwarning("Warning", "Please select a CSV file first!")
            return
        
        if not self.output_folder.get():
            messagebox.showwarning("Warning", "Please select an output folder!")
            return
        
        if self.is_downloading:
            messagebox.showinfo("Info", "Download is already in progress!")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start download in separate thread
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED, bg="#95a5a6")
        self.progress.start(10)
        
        thread = threading.Thread(target=self.download_images, daemon=True)
        thread.start()
    
    def download_images(self):
        csv_file = self.csv_file.get()
        output_folder = self.output_folder.get()
        
        # Create output folder if it doesn't exist
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        # Statistics
        total_images = 0
        downloaded = 0
        failed = 0
        compressed_folders = 0
        start_time = time.time()
        
        self.log(f"📂 Reading CSV file: {csv_file}")
        self.update_status("Reading CSV file...")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                total_products = len(rows)
                processed_products = 0
                
                self.log(f"Found {total_products} products to process\n")
                
                for row in rows:
                    product_id = row.get('id', 'unknown')
                    image_urls = row.get('image', '')
                    
                    if not image_urls:
                        continue
                    
                    # Split multiple URLs (comma-separated)
                    urls = [url.strip() for url in image_urls.split(',') if url.strip()]
                    
                    # Create folder for this product
                    product_folder = Path(output_folder) / product_id
                    product_folder.mkdir(parents=True, exist_ok=True)
                    
                    processed_products += 1
                    
                    # Calculate progress and ETA
                    elapsed_time = time.time() - start_time
                    if processed_products > 0:
                        avg_time_per_product = elapsed_time / processed_products
                        remaining_products = total_products - processed_products
                        eta_seconds = avg_time_per_product * remaining_products
                        eta_minutes = int(eta_seconds // 60)
                        eta_seconds_remainder = int(eta_seconds % 60)
                        progress_percent = (processed_products / total_products) * 100
                        
                        eta_str = f"{eta_minutes}m {eta_seconds_remainder}s" if eta_minutes > 0 else f"{eta_seconds_remainder}s"
                        status_msg = f"Progress: {processed_products}/{total_products} ({progress_percent:.1f}%) | ETA: {eta_str}"
                        self.update_status(status_msg)
                    
                    self.log(f"\n📦 Processing product {processed_products}/{total_products}: {product_id} ({len(urls)} images)")
                    
                    product_download_count = 0
                    
                    for idx, url in enumerate(urls, 1):
                        total_images += 1
                        
                        try:
                            # Extract filename from URL
                            parsed_url = urlparse(url)
                            filename = os.path.basename(parsed_url.path)
                            
                            # If filename is empty, create one
                            if not filename:
                                filename = f"image_{idx}.jpg"
                            
                            # Full path for saving
                            filepath = product_folder / filename
                            
                            # Skip if already downloaded
                            if filepath.exists():
                                self.log(f"  ✓ Already exists: {filename}")
                                downloaded += 1
                                product_download_count += 1
                                continue
                            
                            # Download image
                            self.log(f"  ⬇ Downloading: {filename}")
                            response = requests.get(url, timeout=30)
                            response.raise_for_status()
                            
                            # Save image
                            with open(filepath, 'wb') as img_file:
                                img_file.write(response.content)
                            
                            downloaded += 1
                            product_download_count += 1
                            self.log(f"  ✓ Saved: {filename}")
                            
                            # Be nice to the server
                            time.sleep(0.5)
                            
                        except Exception as e:
                            failed += 1
                            self.log(f"  ✗ Failed: {url}")
                            self.log(f"    Error: {str(e)}")
                    
                    # Compress folder if option is enabled
                    if self.compress_folders.get() and product_download_count > 0:
                        self.log(f"\n🗜️ Compressing folder: {product_id}")
                        
                        # Update status with compression info
                        elapsed_time = time.time() - start_time
                        avg_time_per_product = elapsed_time / processed_products
                        remaining_products = total_products - processed_products
                        eta_seconds = avg_time_per_product * remaining_products
                        eta_minutes = int(eta_seconds // 60)
                        eta_seconds_remainder = int(eta_seconds % 60)
                        eta_str = f"{eta_minutes}m {eta_seconds_remainder}s" if eta_minutes > 0 else f"{eta_seconds_remainder}s"
                        progress_percent = (processed_products / total_products) * 100
                        self.update_status(f"Compressing: {product_id} | Progress: {progress_percent:.1f}% | ETA: {eta_str}")
                        
                        zip_path = Path(output_folder) / f"{product_id}.zip"
                        
                        if self.compress_folder_to_zip(product_folder, zip_path):
                            compressed_folders += 1
                            self.log(f"  ✓ Created ZIP: {product_id}.zip")
                            
                            # Delete original folder if option is enabled
                            if self.delete_after_zip.get():
                                try:
                                    shutil.rmtree(product_folder)
                                    self.log(f"  🗑️ Deleted original folder: {product_id}")
                                except Exception as e:
                                    self.log(f"  ✗ Failed to delete folder: {str(e)}")
            
            # Print summary
            total_time = time.time() - start_time
            total_minutes = int(total_time // 60)
            total_seconds = int(total_time % 60)
            time_str = f"{total_minutes}m {total_seconds}s" if total_minutes > 0 else f"{total_seconds}s"
            
            self.log("\n" + "="*50)
            self.log("📊 DOWNLOAD SUMMARY")
            self.log("="*50)
            self.log(f"Total products processed: {total_products}")
            self.log(f"Total images found: {total_images}")
            self.log(f"Successfully downloaded: {downloaded}")
            self.log(f"Failed: {failed}")
            if self.compress_folders.get():
                self.log(f"Folders compressed: {compressed_folders}")
            self.log(f"Total time: {time_str}")
            self.log(f"Images saved in: {output_folder}/")
            self.log("="*50)
            
            summary_msg = f"Download completed!\n\nProducts: {total_products}\nTotal: {total_images}\nDownloaded: {downloaded}\nFailed: {failed}"
            if self.compress_folders.get():
                summary_msg += f"\nCompressed: {compressed_folders} folders"
            summary_msg += f"\n\nTime taken: {time_str}"
            
            self.update_status(f"Completed! Downloaded: {downloaded}, Failed: {failed}")
            messagebox.showinfo("Success", summary_msg)
            
        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}")
            self.update_status("Error occurred during download")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.is_downloading = False
            self.download_btn.config(state=tk.NORMAL, bg="#27ae60")
            self.progress.stop()

def main():
    root = tk.Tk()
    app = ImageDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
