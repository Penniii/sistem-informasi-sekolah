// Menambahkan tombol "mata" (lihat/sembunyikan) di setiap isian password.

const IKON_MATA = `
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
       fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>`;

const IKON_MATA_CORET = `
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
       fill="none" stroke="currentColor" stroke-width="2"
       stroke-linecap="round" stroke-linejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>`;

document.querySelectorAll('input[type="password"]').forEach(function (input) {
  // 1. Bungkus isian dengan sebuah div, supaya tombol bisa diletakkan di atasnya
  const pembungkus = document.createElement('div');
  pembungkus.className = 'kotak-password';
  input.parentNode.insertBefore(pembungkus, input);
  pembungkus.appendChild(input);

  // 2. Buat tombol mata
  const tombol = document.createElement('button');
  tombol.type = 'button';
  tombol.className = 'tombol-mata';
  tombol.setAttribute('aria-label', 'Tampilkan password');
  tombol.innerHTML = IKON_MATA;
  pembungkus.appendChild(tombol);

  // 3. Saat tombol diklik, tukar jenis isian antara password dan text
  tombol.addEventListener('click', function () {
    const sedangTersembunyi = input.type === 'password';
    input.type = sedangTersembunyi ? 'text' : 'password';
    tombol.innerHTML = sedangTersembunyi ? IKON_MATA_CORET : IKON_MATA;
    tombol.setAttribute(
      'aria-label',
      sedangTersembunyi ? 'Sembunyikan password' : 'Tampilkan password'
    );
  });
});

