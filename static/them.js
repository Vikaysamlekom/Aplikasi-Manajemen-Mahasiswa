const toggle = document.getElementById('themeToggle');

function applyTheme(theme){
    if(theme === 'dark'){
        document.body.classList.add('dark');
        toggle.textContent = 'Light';
    } else {
        document.body.classList.remove('dark');
        toggle.textContent = 'Dark';
    }
}

// Event toggle button
toggle.addEventListener('click', () => {
    const current = document.body.classList.contains('dark') ? 'dark' : 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', next); // simpan preferensi
    applyTheme(next);
});

// Saat halaman dibuka, ambil dari localStorage
applyTheme(localStorage.getItem('theme') || 'light');
