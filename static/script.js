// Keyboard navigation for top nav: first letter = section, H = home, U = back
document.addEventListener('keydown', function(e) {
	// Ignore if typing in input/textarea
	if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
	if (e.ctrlKey || e.metaKey || e.altKey) return;

	// H = home
	if (e.key === 'h' || e.key === 'H') {
		window.location.href = '/';
		return;
	}

	// U = back (scroll to top first, then go back)
	if (e.key === 'u' || e.key === 'U') {
		e.preventDefault();
		const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
		// If already at top (within 10px), go back
		if (scrollPosition <= 10) {
			window.history.back();
		} else {
			// Otherwise scroll to top
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
		return;
	}

	// Find nav links
	const navLinks = Array.from(document.querySelectorAll('.nav__list .link--nav'));
	if (!navLinks.length) return;
	const pressed = e.key.toLowerCase();
	// Find first nav link whose text starts with pressed key
	const match = navLinks.find(link => link.textContent.trim().toLowerCase().startsWith(pressed));
	if (match) {
		window.location.href = match.href;
	}
});
const body = document.body

const btnTheme = document.querySelector('.fa-moon')
const btnHamburger = document.querySelector('.fa-bars')

const addThemeClass = (bodyClass, btnClass) => {
  body.classList.add(bodyClass)
  btnTheme.classList.add(btnClass)
}

const getBodyTheme = localStorage.getItem('portfolio-theme')
const getBtnTheme = localStorage.getItem('portfolio-btn-theme')

addThemeClass(getBodyTheme, getBtnTheme)

const isDark = () => body.classList.contains('dark')

const setTheme = (bodyClass, btnClass) => {

	body.classList.remove(localStorage.getItem('portfolio-theme'))
	btnTheme.classList.remove(localStorage.getItem('portfolio-btn-theme'))

  addThemeClass(bodyClass, btnClass)

	localStorage.setItem('portfolio-theme', bodyClass)
	localStorage.setItem('portfolio-btn-theme', btnClass)
}

const toggleTheme = () =>
	isDark() ? setTheme('light', 'fa-moon') : setTheme('dark', 'fa-sun')

btnTheme.addEventListener('click', toggleTheme)

const displayList = () => {
	const navUl = document.querySelector('.nav__list')

	if (btnHamburger.classList.contains('fa-bars')) {
		btnHamburger.classList.remove('fa-bars')
		btnHamburger.classList.add('fa-times')
		navUl.classList.add('display-nav-list')
	} else {
		btnHamburger.classList.remove('fa-times')
		btnHamburger.classList.add('fa-bars')
		navUl.classList.remove('display-nav-list')
	}
}

btnHamburger.addEventListener('click', displayList)

const scrollUp = () => {
	const btnScrollTop = document.querySelector('.scroll-top')

	if (
		body.scrollTop > 500 ||
		document.documentElement.scrollTop > 500
	) {
		btnScrollTop.style.display = 'block'
	} else {
		btnScrollTop.style.display = 'none'
	}
}

document.addEventListener('scroll', scrollUp)

// clipboard.js
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("a[data-clipboard]").forEach(link => {
        link.addEventListener("click", async (e) => {
            e.preventDefault(); // prevent navigation
            const text = link.getAttribute("data-clipboard");
            try {
                await navigator.clipboard.writeText(text);
            } catch (err) {
                console.error("Clipboard copy failed", err);
            }
        });
    });
});