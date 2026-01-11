/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#3B82F6',      // 主色調（藍色）
        success: '#10B981',      // 成功（綠色）
        danger: '#EF4444',       // 危險（紅色）
        warning: '#F59E0B',      // 警告（黃色）
        muted: '#6B7280',        // 次要文字
      },
    },
  },
  plugins: [],
}
