const galleryImages = document.querySelectorAll(".gallery-image");

const lightbox = document.getElementById("lightbox");

const lightboxImage = document.getElementById("lightbox-image");

const close = document.querySelector(".close");

galleryImages.forEach(image => {

    image.addEventListener("click", () => {

        lightbox.style.display = "flex";
        lightboxImage.src = image.src;

    });

});

close.addEventListener("click", () => {

    lightbox.style.display = "none";

});

lightbox.addEventListener("click", (event) => {

    if (event.target === lightbox) {

        lightbox.style.display = "none";

    }

});