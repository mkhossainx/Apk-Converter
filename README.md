# 🚀 APK Converter (APKS/APKM/XAPK → APK)

A modern Flask-based web application that converts **.APKS**, **.APKM**, and **.XAPK** files into a single installable **.APK**.

Designed with a modern responsive UI and automatic Bundletool download.

---

## ✨ Features

- ✅ Convert `.apks` → `.apk`
- ✅ Convert `.apkm` → `.apk`
- ✅ Convert `.xapk` → `.apk`
- ✅ Auto downloads latest Bundletool
- ✅ Modern Glassmorphism UI
- ✅ Drag & Drop Upload
- ✅ Mobile Friendly
- ✅ No manual Bundletool installation required
- ✅ Automatic cleanup after download

---

# 📷 Supported Formats

| Input | Output |
|--------|---------|
| APKS | APK |
| APKM | APK |
| XAPK | APK |

---

# 📦 Requirements

- Python 3.9+
- Java 11 or newer

Check versions

```bash
python --version
```

```bash
java -version
```

---

# 📥 Installation

Clone repository

```bash
git clone https://github.com/mkhossainx/apk-converter.git
```

Go inside project

```bash
cd apk-converter
```

Install dependencies

```bash
pip install -r requirements.txt
```

or

```bash
pip install flask requests
```

---

# ▶️ Run

Simply execute

```bash
python app.py
```

The application will automatically:

- Create upload folder
- Create output folder
- Download latest Bundletool (only first run)

After starting you'll see

```
🔥 MKxHACKER APK Converter started at

http://127.0.0.1:5000
```

Open your browser

```
http://127.0.0.1:5000
```

---

# 🌐 Using the Website

## Step 1

Open

```
http://localhost:5000
```

---

## Step 2

Upload one of:

- .apks
- .apkm
- .xapk

You can

- Tap upload area
- Drag & Drop file

---

## Step 3

Press

```
Convert
```

The converter will automatically

- Detect file type
- Extract archive
- Merge Split APKs
- Generate APK

---

## Step 4

When conversion finishes

Click

```
Download
```

Your APK will be downloaded automatically.

---

# ⚙️ How It Works

## APKS/APKM

The application

1. Extracts archive
2. Finds split APKs
3. Uses Google Bundletool
4. Merges into one APK

If Bundletool fails:

- Fallback method is used
- Base APK is extracted

---

## XAPK

The application

1. Opens XAPK
2. Finds APK
3. Extracts it
4. Downloads APK

---

# 📁 Project Structure

```
project/

│
├── app.py
├── uploads/
├── outputs/
├── bundletool.jar
└── README.md
```

---

# 📂 Upload Size

Maximum upload size

```
500 MB
```

Can be changed here

```python
MAX_CONTENT_LENGTH = 500 * 1024 * 1024
```

---

# 🔧 Environment Variable (Optional)

If Bundletool already exists

Set

```
BUNDLETOOL_PATH
```

Example

Linux

```bash
export BUNDLETOOL_PATH=/home/user/bundletool.jar
```

Windows

```cmd
set BUNDLETOOL_PATH=C:\bundletool.jar
```

Otherwise application downloads automatically.

---

# ❗Common Errors

## Java not installed

Error

```
java: command not found
```

Install Java 11+

---

## Unsupported Format

Upload only

```
.apks
.apkm
.xapk
```

---

## Bundletool Download Failed

Possible reasons

- No internet
- GitHub blocked
- Firewall

Download manually

Rename

```
bundletool.jar
```

Place beside

```
app.py
```

---

## No Split APK Found

Your archive may be corrupted.

Try downloading it again.

---

# 🔒 Privacy

- Files are processed locally.
- Uploaded files are automatically deleted.
- Generated APK is removed after download.
- No database is used.

---

# 🚀 Technologies

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- Google Bundletool

---

# ❤️ Credits

Developed by

**MK Hossain**

Telegram

```
https://t.me/mk_hossain
```

---

# ⚠ Disclaimer

This project is intended for educational and personal use only.

Some applications use advanced split APK protection and may not be mergeable into a single APK.

The developer is not responsible for misuse of this software.

---

# ⭐ Support

If you like this project

⭐ Star the repository

Share it with your friends.

Happy Converting ❤️
