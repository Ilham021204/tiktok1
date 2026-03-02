#!/data/data/com.termux/files/usr/bin/python

import subprocess
import json
import time
import os
import sys
import requests
from datetime import datetime
from colorama import init, Fore, Style

# Inisialisasi colorama untuk output berwarna
init(autoreset=True)

# Konfigurasi
PHONE_NUMBER = "085338075301"  # Ganti dengan nomor WhatsApp tujuan
CHECK_INTERVAL = 2  # Detik
SMS_LOG = "forwarded_sms.log"

# Banner
def show_banner():
    os.system('clear')
    print(Fore.CYAN + "="*60)
    print(Fore.YELLOW + "   TIKTOK SMS FORWARDER - TERMUX EDITION")
    print(Fore.CYAN + "="*60)
    print(Fore.GREEN + f"[✓] Target Number: {PHONE_NUMBER}")
    print(Fore.GREEN + f"[✓] Check Interval: {CHECK_INTERVAL} detik")
    print(Fore.CYAN + "="*60)

# Fungsi membaca SMS dengan Termux API
def get_recent_sms(limit=20):
    try:
        # Gunakan termux-sms-list untuk mengambil SMS terbaru
        result = subprocess.run(
            ['termux-sms-list', '-l', str(limit)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout:
            sms_list = json.loads(result.stdout)
            return sms_list
        else:
            print(Fore.RED + "❌ Gagal membaca SMS")
            return []
    
    except json.JSONDecodeError as e:
        print(Fore.RED + f"❌ Error parsing JSON: {e}")
        return []
    except subprocess.TimeoutExpired:
        print(Fore.RED + "❌ Timeout membaca SMS")
        return []
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")
        return []

# Deteksi SMS TikTok
def is_tiktok_sms(sms):
    keywords = ['tiktok', 'tik tok', 'kode', 'verifikasi', 'code', 'verification', 
                'login', 'masuk', 'otp', 'sandi', 'password']
    
    body_lower = sms.get('body', '').lower()
    
    # Cek apakah mengandung kata kunci TikTok
    if any(keyword in body_lower for keyword in keywords):
        # Verifikasi tambahan untuk memastikan ini SMS verifikasi
        if any(num in body_lower for num in ['kode', 'code', 'otp', 'verifikasi']):
            return True
    
    return False

# Kirim notifikasi ke Termux (bisa dilihat di notifikasi Android)
def send_termux_notification(title, message):
    try:
        subprocess.run(
            ['termux-notification', '--title', title, '--content', message, '--priority', 'high'],
            timeout=5
        )
    except:
        pass

# Kirim ke WhatsApp menggunakan Termux
def send_to_whatsapp(message, sms_details):
    try:
        # Format pesan untuk WhatsApp
        formatted_msg = f"""🔐 *KODE VERIFIKASI TIKTOK*
        
📱 *Dari:* {sms_details.get('sender', 'Unknown')}
⏰ *Waktu:* {sms_details.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
📝 *Pesan:*
{message}

━━━━━━━━━━━━━━━━━━━━━
💡 *Forwarder SMS Aktif*
"""
        
        # Simpan ke file log dulu
        with open('temp_msg.txt', 'w', encoding='utf-8') as f:
            f.write(formatted_msg)
        
        # Gunakan termux-clipboard untuk copy pesan
        subprocess.run(['termux-clipboard-set', formatted_msg], timeout=5)
        
        # Buka WhatsApp langsung
        whatsapp_intent = f'am start -a android.intent.action.VIEW -d "https://wa.me/{PHONE_NUMBER}?text={requests.utils.quote(formatted_msg)}"'
        subprocess.run(whatsapp_intent, shell=True, timeout=10)
        
        # Alternatif: buka kontak spesifik
        # whatsapp_contact = f'am start -a android.intent.action.VIEW -d "content://com.android.contacts/data/{CONTACT_ID}"'
        
        return True
        
    except Exception as e:
        print(Fore.RED + f"❌ Gagal kirim WhatsApp: {e}")
        return False

# Simpan log SMS yang sudah diforward
def log_forwarded_sms(sms_id, sms_body):
    try:
        with open(SMS_LOG, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} | {sms_id} | {sms_body[:100]}...\n")
    except:
        pass

# Baca log SMS yang sudah diforward
def get_forwarded_ids():
    forwarded_ids = set()
    try:
        if os.path.exists(SMS_LOG):
            with open(SMS_LOG, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(' | ')
                    if len(parts) >= 2:
                        forwarded_ids.add(parts[1])
    except:
        pass
    return forwarded_ids

# Fungsi utama monitoring
def monitor_sms():
    show_banner()
    
    print(Fore.CYAN + "\n[SYSTEM] Memulai monitoring SMS TikTok...")
    print(Fore.CYAN + "[SYSTEM] Tekan Ctrl+C untuk berhenti\n")
    
    # Load ID SMS yang sudah diforward
    forwarded_ids = get_forwarded_ids()
    last_check = {}
    
    try:
        while True:
            # Ambil SMS terbaru
            sms_messages = get_recent_sms(30)  # Ambil 30 SMS terbaru
            
            for sms in sms_messages:
                # Buat ID unik untuk SMS
                sms_id = f"{sms.get('received', '')}_{sms.get('body', '')[:50]}"
                
                # Cek apakah ini SMS TikTok dan belum diforward
                if is_tiktok_sms(sms) and sms_id not in forwarded_ids:
                    
                    # Warna hijau untuk SMS TikTok
                    print(Fore.GREEN + "\n" + "="*60)
                    print(Fore.GREEN + "🔔 TIKTOK SMS DITEMUKAN!")
                    print(Fore.GREEN + "="*60)
                    print(Fore.WHITE + f"Dari: {sms.get('sender', 'Unknown')}")
                    print(Fore.WHITE + f"Waktu: {sms.get('received', 'Unknown')}")
                    print(Fore.WHITE + f"Isi: {sms.get('body', '')}")
                    print(Fore.GREEN + "="*60)
                    
                    # Kirim notifikasi Termux
                    send_termux_notification(
                        "🔐 Kode Verifikasi TikTok!", 
                        sms.get('body', '')
                    )
                    
                    # Siapkan detail SMS
                    sms_details = {
                        'sender': sms.get('sender', 'Unknown'),
                        'time': sms.get('received', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        'body': sms.get('body', '')
                    }
                    
                    # Tanya user apakah ingin forward (opsional)
                    print(Fore.YELLOW + "\n🔄 Forward ke WhatsApp? (y/n): ", end='')
                    # Untuk auto-forward tanpa konfirmasi, hapus baris di bawah
                    # choice = input().lower()
                    choice = 'y'  # Auto-forward
                    
                    if choice == 'y':
                        success = send_to_whatsapp(sms.get('body', ''), sms_details)
                        
                        if success:
                            print(Fore.GREEN + "✅ Berhasil dikirim ke WhatsApp!")
                            forwarded_ids.add(sms_id)
                            log_forwarded_sms(sms_id, sms.get('body', ''))
                        else:
                            print(Fore.RED + "❌ Gagal mengirim ke WhatsApp")
                    
                    print(Fore.CYAN + "\n[SYSTEM] Melanjutkan monitoring...")
            
            # Tunggu sebelum cek lagi
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⏹️ Monitoring dihentikan oleh user")
        print(Fore.CYAN + f"Total SMS TikTok terdeteksi: {len(forwarded_ids)}")
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"\n❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    monitor_sms()
