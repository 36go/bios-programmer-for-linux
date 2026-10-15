# مبرمج البيوس لنظام لينكس

[![اللغة: العربية](https://img.shields.io/badge/lang-AR-16a34a?style=flat-square)](README.ar.md)
[![Language: English](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)](README.md)
[![الرخصة: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![المنصة: لينكس](https://img.shields.io/badge/platform-Linux-333.svg)](#المتطلبات)

نسخة **لينكس أصلية من برنامج [AsProgrammer / NeoProgrammer](https://github.com/nofeletru/UsbAsp-flash)** — أداة بواجهة رسومية لقراءة وكتابة ومحو والتحقق من شرائح الذاكرة عبر بروتوكولات **SPI** و **I2C** و **MicroWire**، تمامًا مثل برامج "مبرمج CH341A" على ويندوز.

المشروع الأصلي يتعامل مع العتاد عبر مكتبات ويندوز (`CH341DLL.DLL` و`CH347DLL.DLL` و`FTD2XX.DLL`). هذه النسخة **تزيل الاعتماد على مكتبات DLL وتعيد تنفيذ واجهة CH341 مباشرةً على `libusb`**، بحيث تُبنى وتعمل على لينكس (بما في ذلك WSL2 مع WSLg) بنفس الواجهة الرسومية ونفس نموذج `chiplist.xml` والإعدادات.

![مبرمج البيوس لنظام لينكس يعمل تحت WSLg](images.png)

---

## المحتويات

- [المزايا](#المزايا)
- [العتاد المدعوم](#العتاد-المدعوم)
- [المتطلبات](#المتطلبات)
- [البناء من المصدر](#البناء-من-المصدر)
- [التشغيل](#التشغيل)
- [بنية المشروع](#بنية-المشروع)
- [كيفية استبدال مكتبات ويندوز](#كيفية-استبدال-مكتبات-ويندوز)
- [الحالة والقيود المعروفة](#الحالة-والقيود-المعروفة)
- [المساهمة](#المساهمة)
- [الشكر والتقدير](#الشكر-والتقدير)
- [الرخصة](#الرخصة)

---

## المزايا

- **واجهة رسومية** كاملة بتقنية Lazarus/GTK2 (بنفس تخطيط نسخة ويندوز).
- قراءة / كتابة / التحقق / المحو لشرائح EEPROM والفلاش.
- البروتوكولات: **SPI 25** و **SPI 45** و **SPI 95** و **I2C** و **MicroWire**.
- قاعدة بيانات ضخمة للشرائح (`chiplist.xml`) مع كشف تلقائي للشريحة (JEDEC ID / CFI).
- محرر ست عشري مع تعبئة / مقارنة / تفريغ، وبحث، ومحرر سجلات.
- محرّك نصوص برمجية (`scripts/`) لكتابة إجراءات مخصصة للشرائح.
- ترجمات متعددة للواجهة (`lang/*.po`).

## العتاد المدعوم

| المبرمج | الحالة على لينكس | ملاحظات |
|---|---|---|
| **CH341A / CH341** | ✅ **مُنفَّذ** | أُعيد تنفيذه على `libusb` (نقاط النهاية `0x02`/`0x82`). غير مُختبَر على عتاد حقيقي لعدم توفّر جهاز أثناء عملية النقل. |
| USBasp | ✅ متوقع أن يعمل | يستخدم واجهة `libusb` الموجودة أصلًا في المشروع. |
| AVRISP-MKII | ✅ متوقع أن يعمل | يستخدم واجهة `libusb` الموجودة أصلًا في المشروع. |
| Arduino (تسلسلي) | ✅ متوقع أن يعمل | يستخدم واجهة التسلسل المحمولة (`synaser`). |
| **CH347** | ⚠️ ليس بعد | استُبدلت استدعاءات DLL بدوال فارغة ليكتمل البناء فقط؛ غير مُنفَّذ. |
| **FT232H** | ⚠️ ليس بعد | استُبدلت استدعاءات `FTD2XX` بدوال فارغة؛ غير مُنفَّذ. |

> إذا كان لديك عتاد CH341 فسيكون الاختبار والإبلاغ عن الأخطاء موضع ترحيب كبير — راجع [المساهمة](#المساهمة).

## المتطلبات

- سطح مكتب لينكس (X11 أو Wayland مع XWayland) — مجموعة أدوات GTK2 افتراضيًا.
- **[Free Pascal Compiler](https://www.freepascal.org/) 3.2+** و **[Lazarus](https://www.lazarus-ide.org/)** (`lazbuild`).
- ملفات تطوير **`libusb-0.1`** (`libusb-dev` / `libusb-0.1-4`).
- ملفات تطوير GTK2 (`libgtk2.0-dev`) *أو* Qt5 (`libqt5pas-dev`).
- حزم Lazarus: **TurboPowerIPro** و **SynEdit** و **mphexeditor**.

على Debian/Ubuntu (بما في ذلك WSL):

```bash
sudo apt update
sudo apt install fpc lazarus libusb-dev libgtk2.0-dev python3
```

## البناء من المصدر

```bash
git clone https://github.com/36go/bios-programmer-for-linux.git
cd bios-programmer-for-linux/src

# (مرة واحدة) ثبّت حزم Lazarus الثلاث المطلوبة، مثال:
#   lazbuild --add-package-link /usr/lib/lazarus/*/components/synedit/synedit.lpk
#   ... بالإضافة إلى TurboPowerIPro و mphexeditor

lazbuild AsProgrammer.lpi
./AsProgrammer
```

ملف المشروع (`AsProgrammer.lpi`) مُهيّأ مسبقًا لـ **لينكس / x86_64 / GTK2**، مع إخراج الملفات في `lang/` والوحدات في `lib/`.

## التشغيل

يحمّل البرنامج ملفات `chiplist.xml` و`settings.xml` ومجلدات `scripts/` و`icons/` من **مجلد العمل الحالي**، لذا شغّله من داخل `src/`:

```bash
cd src
./AsProgrammer
```

**صلاحيات CH341:** في معظم التوزيعات يكون ملف الجهاز محصورًا على root. أنشئ قاعدة udev ليتمكّن المستخدم العادي من الوصول إليه (`1a86:5512`):

```bash
sudo tee /etc/udev/rules.d/99-ch341a.rules <<'EOF'
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="5512", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="1a86", ATTR{idProduct}=="5523", MODE="0666"
EOF
sudo udevadm control --reload-rules && sudo udevadm trigger
```

كما تحاول الواجهة تلقائيًا فصل تعريف النواة `spi-ch341`/`ch341` إذا كان قد استحوذ على الجهاز.

## بنية المشروع

```
.
├── src/                 # مصادر التطبيق (يُبنى من هنا)
│   ├── AsProgrammer.lpi # مشروع Lazarus (لينكس/x86_64/GTK2)
│   ├── ch341dll.pas     # واجهة CH341 أُعيد تنفيذها على libusb  <-- نقل
│   ├── ch347dll.pas     # استدعاءات CH347 -> دوال فارغة            <-- نقل
│   ├── D2XXUnit.pas     # استدعاءات FTDI D2XX -> دوال فارغة       <-- نقل
│   ├── LibUSB01.pas     # ارتباطات libusb-0.1
│   ├── chiplist.xml     # قاعدة بيانات الشرائح
│   ├── lang/ icons/ scripts/
│   └── ...
├── tools/               # سكربتات إزالة/إعادة كتابة ارتباطات DLL
├── docs/PORTING_NOTES.md
├── images.png           # الصورة المستخدمة في هذا الملف
└── LICENSE
```

## كيفية استبدال مكتبات ويندوز

يصرّح الكود الأصلي بكل استدعاء للعتاد عبر ارتباط `external '....DLL'`، وهو ما يرفضه رابط لينكس. تعيد هذه النسخة كتابة وحدات الارتباط الثلاث (انظر `docs/PORTING_NOTES.md` و`tools/`):

- **`ch341dll.pas`** — أُزيلت كل جمل `external`. الدوال العشر المستخدمة فعليًا في `ch341hw.pas` أُعيد تنفيذها بلغة Pascal فوق `LibUSB01` (libusb-0.1): الفتح/الإغلاق بمعرّف `1a86` / `5512` (أو `5523`)، والكتابة عبر EP `0x02`، والقراءة من EP `0x82`، وتأطير تدفّق SPI `0xA8`، وتجهيز التدفّق `0xAA`، وتسلسل اختيار الشريحة `0xAB` (UIO). تُركت بقية الدوال كدوال فارغة آمنة.
- **`ch347dll.pas`** — استُبدلت كل الارتباطات بدوال فارغة (الواجهة غير مُنفَّذة بعد).
- **`D2XXUnit.pas`** — استُبدلت كل الارتباطات بدوال فارغة مضمّنة (واجهة FT232H غير مُنفَّذة بعد).

لإعادة تطبيق التعديلات على نسخة نظيفة من المصدر الأصلي:

```bash
UPSTREAM=/path/to/AsProgrammer/software ./tools/apply_shims.sh ./src
```

## الحالة والقيود المعروفة

- ✅ **يُبنى** بنجاح عبر `lazbuild` و**يُشغّل** كواجهة GTK2.
- ✅ مسار **قراءة/كتابة SPI** لـ CH341 مُنفَّذ وفق تعريف `spi-ch341` في نواة لينكس وتأطير مشروع `ch341prog`.
- ⚠️ طُوِّرت النسخة **دون مبرمج فعلي**، لذا مسار CH341 غير مُتحقَّق منه على عتاد حقيقي.
- ⚠️ دوال I2C (`CH341StreamI2C`) وMicroWire (`CH341BitStreamSPI`) و`CH341SetOutput` و`CH341GetStatus` هي **محاولات مبدئية** والأكثر احتمالًا لاحتياجها تصحيحات بسيطة على العتاد.
- ⚠️ واجهتا CH347 وFT232H دوال فارغة حاليًا.

## المساهمة

**هذا المشروع مفتوح للمساهمة — نرحّب بشدة بطلبات السحب (Pull Requests) والملاحظات!** 🎉

أفضل نقاط للبدء:

1. **الاختبار على عتاد حقيقي.** إذا كنت تملك CH341A، جرّب القراءة/التحقق/الكتابة على شريحة معروفة وأبلغنا بالنتائج (طراز الشريحة، التوزيعة، السجلّات). هذه أنفع مساهمة على الإطلاق.
2. **تنفيذ واجهة CH347** (`ch347dll.pas`) — جاهزة كدوال فارغة بانتظار تنفيذها على `libusb`.
3. **تنفيذ واجهة FT232H** (`D2XXUnit.pas`) عبر `libusb`.
4. **تحسين مسارات I2C / MicroWire** (`CH341StreamI2C` و`CH341BitStreamSPI` و`CH341SetOutput` و`CH341GetStatus`).
5. **الترجمات** — أضف أو حسّن ملفات `src/lang/*.po`.
6. **التغليف** — حزم AppImage / Flatpak / Debian، أو ملف `Makefile` بسيط.

كيف تساهم:

```bash
# ١. اعمل Fork ثم استنساخ
git clone https://github.com/<you>/bios-programmer-for-linux.git
# ٢. أنشئ فرعًا
git checkout -b feature/my-fix
# ٣. ابنِ واختبر
cd src && lazbuild AsProgrammer.lpi
# ٤. التزم، وادفع، وافتح طلب سحب (Pull Request)
```

يرجى الحفاظ على أسلوب الكود الأصلي، ووصف أي عتاد اختبرته عليه في طلب السحب.

## الشكر والتقدير

- التطبيق الأصلي **AsProgrammer / NeoProgrammer** من إعداد **nofeletru** — <https://github.com/nofeletru/UsbAsp-flash>.
- مراجع بروتوكول CH341 عبر USB: ملف `drivers/spi/spi-ch341.c` في نواة لينكس ومشروع `ch341prog`.
- نسخة لينكس وواجهة libusb وإصلاحات البناء: **36go**.

## الرخصة

صادر تحت **رخصة MIT** — راجع [LICENSE](LICENSE). العمل الأصلي © 2015 nofeletru؛ نسخة لينكس © 2026 36go.

---

[![اللغة: العربية](https://img.shields.io/badge/lang-AR-16a34a?style=flat-square)](README.ar.md)
[![Language: English](https://img.shields.io/badge/lang-EN-2563eb?style=flat-square)](README.md)
