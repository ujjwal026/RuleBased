# Rule-Based
<<<<<<< HEAD
# Rule-Filter_based# Rule-Based
# Installation & Dependencies

## Backend (Flask)

### Install Dependencies
```sh
pip install flask flask-cors
```

### Run the Backend
```sh
python app.py
```

## Frontend (React + Vite)

### Create a Vite Project
```sh
npm create vite@latest frontend --template react
cd frontend
```

### Install Dependencies
```sh
npm install
```

### Set Up Tailwind CSS
```sh
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Modify `tailwind.config.js`:
```js
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

Modify `src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Run the Frontend
```sh
npm run dev
```

=======
# Rule-Based
>>>>>>> 8060c25ecbc77d9962e0edbbacda3e6a1f1cd171
