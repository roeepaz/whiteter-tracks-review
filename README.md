# פרויקט מלבין נתיבים

---

## 🎞️ דרישות מערכת
- Python 3.10 ומעלה
- pip
- Node.js 18 ומעלה (Frontend)

---

## 🛠️ התקנת הפרויקט

### 1. clone
```bash
git clone https://github.com/your-username/whitener-paths.git
cd whitener-paths
```

### 2. יצירת סביבת עבודה וירטואלית
```bash
python -m venv .venv
```

### 3. הפעלת הסביבה
- ב-Windows:
```bash
.\.venv\Scripts\activate
```

- ב-Mac/Linux:
```bash
source .venv/bin/activate
```

### 4. התקנת התלויות
```bash
pip install -r requirements.txt
```

### 5. הרצת השרת Flask
```bash
cd back-end
python src/main.py
```

### 6. התקנת והרצת ה-Front-End (React)
```bash
cd ../front-end/my-app
npm install
npm run dev
```
### 7. התאמת קובץ הקונפיגורציה app_config
הגדר מה שמתאים לך, קודם כל את הpath לתיקיית הקבצים
---

Configuration
All server‐side config lives in back-end/resource/app_config.yaml (or .json).
Use config_loader.get_config_value(key) in code to access values.

## Documentation

- **Flask App Overview**: [back-end/docs/flask_overview.md](back-end/docs/flask_overview.md)

API Endpoints:

GET /health

GET /api/events

GET /api/get-event/<event_id>

POST /creat-track

POST /submit-event

POST /get-recommendation


## 🧐 הקדמה

פרויקט "מלבין נתיבים" נועד לשפר את יכולת ניתוח ופענוח נתיבים והתנהגויות של כלי טיס או חפצים בשמיים, על בסיס נתוני מכԭם גולמיים.

מטרת הפרויקט היא להפוך נתונים גולמיים למידע חוזי ואינטואיטיבי על מפות, באמצעות סינון, אופטימוזציה וקיבוץ, וכוללת מודול המלצות אוטומטי לתמיכה בהכרעות וניתוח אירועים.

---

## 🌟 מטרות ויעדים

- איסוף ועיבוד נתונים: קליטת קבצים (plots.csv, plot_correlations.csv), ניקוי והמרה לנורמליזציה.
- פענוח נתיבים: זיהוי וניקוי נקודות, עיבוד עם Spline ליצירת נתיב חלק.
- קיבוץ ואשכלות: זיהוי קבוצות בנתונים אמיתיים ע"י DBSCAN.
- מערכת המלצות: הפקת המלצות אוטומטיות לניתוח ותמיכה.

---

## 🔧 התקשרות בין המערכות

- ה-Front-End (React) רוץ על http://localhost:5173
- ה-Back-End (Flask) רוץ על http://localhost:5000
- React שולח בקשות HTTP ל-API של Flask.

---

## 🔧 תרומות ותחזוק

- אנא לדווח על תקלות או הצעות שיפות באתר ה-Issues ב-GitHub.
- מסמכים ותיעוד נוספו בקוד.

---

## 🏃‍♂️ סיכום

הפרויקט משלב כושרות עיבוד נתונים, אלגוריתמי ניתוח וממשק אינטראקטיבי, כל זה בקוד פתוח.

---

Developed with ❤️ by Roee — Clean Git, Clear Code, Pure Power.
