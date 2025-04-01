/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#00693E", // Green header
        lightGrey: "#F0F0F0", // Light grey background
        darkChat: "#1E1E1E", // Dark chat box
      },
    },
  },
  plugins: [],
};
