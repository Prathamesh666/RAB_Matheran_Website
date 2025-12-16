// Smooth Scroll for Navigation Links
document.querySelectorAll('nav a').forEach(anchor => {
  anchor.addEventListener('click', function(e) {
    e.preventDefault();
    const targetId = this.getAttribute('href').substring(1);
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      targetElement.scrollIntoView({ behavior: 'smooth' });
    }
  });
});

// Mobile Menu Toggle
const menuToggle = document.getElementById('menu-toggle');
const navMenu = document.getElementById('nav-menu');

if (menuToggle) {
  menuToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
  });
}

// Gallery Lightbox
const galleryImages = document.querySelectorAll('.gallery img');
galleryImages.forEach(img => {
  img.addEventListener('click', () => {
    const lightbox = document.createElement('div');
    lightbox.id = 'lightbox';
    lightbox.style.position = 'fixed';
    lightbox.style.top = 0;
    lightbox.style.left = 0;
    lightbox.style.width = '100%';
    lightbox.style.height = '100%';
    lightbox.style.background = 'rgba(0,0,0,0.8)';
    lightbox.style.display = 'flex';
    lightbox.style.alignItems = 'center';
    lightbox.style.justifyContent = 'center';
    lightbox.style.zIndex = 1000;

    const imgClone = img.cloneNode();
    imgClone.style.maxWidth = '90%';
    imgClone.style.maxHeight = '90%';
    lightbox.appendChild(imgClone);

    document.body.appendChild(lightbox);

    lightbox.addEventListener('click', () => {
      document.body.removeChild(lightbox);
    });
  });
});

// Booking Form Validation
const bookingForm = document.getElementById('booking-form');
if (bookingForm) {
  bookingForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const name = this.querySelector('[name="name"]').value.trim();
    const email = this.querySelector('[name="email"]').value.trim();
    const date = this.querySelector('[name="date"]').value.trim();

    if (!name || !email || !date) {
      alert("Please fill out all required fields.");
      return;
    }

    // Simple email validation
    const emailPattern = /^[^ ]+@[^ ]+\.[a-z]{2,3}$/;
    if (!email.match(emailPattern)) {
      alert("Please enter a valid email address.");
      return;
    }

    alert("Thank you for booking! We'll contact you soon.");
    this.reset();
  });
}

// Scroll-to-Top Button
const scrollBtn = document.getElementById('scroll-top');
window.addEventListener('scroll', () => {
  if (window.scrollY > 300) {
    scrollBtn.style.display = 'block';
  } else {
    scrollBtn.style.display = 'none';
  }
});

if (scrollBtn) {
  scrollBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// Gallery Edit for delete confirmation
  let targetForm = null;

  // Capture which form triggered the modal
  document.querySelectorAll('[data-bs-target="#confirmDeleteModal"]').forEach(btn => {
    btn.addEventListener('click', function() {
      targetForm = this.closest('form');
    });
  });

  // When confirm button is clicked, submit the stored form
  document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
    if (targetForm) {
      targetForm.submit();
    }
  });

//Lazy loading + modal script 
document.addEventListener("DOMContentLoaded", function() {
  // Lazy load images
  const lazyImages = [].slice.call(document.querySelectorAll("img.lazy"));
  if ("IntersectionObserver" in window) {
    let lazyObserver = new IntersectionObserver(function(entries, observer) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          let img = entry.target;
          img.src = img.dataset.src;
          img.classList.remove("lazy");
          lazyObserver.unobserve(img);
        }
      });
    });
    lazyImages.forEach(function(img) { lazyObserver.observe(img); });
  } else {
    lazyImages.forEach(function(img) { img.src = img.dataset.src; });
  }

  // Modal image handler
  const modalImage = document.getElementById("modalImage");
  document.querySelectorAll("[data-bs-target='#imageModal']").forEach(img => {
    img.addEventListener("click", function() {
      modalImage.src = this.getAttribute("data-full");
    });
  });
});