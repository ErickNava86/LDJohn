const galleryImages = document.querySelectorAll(".gallery-image");

if (galleryImages.length > 0) {

    galleryImages.forEach((image, index) => {

        image.addEventListener("click", () => {

            currentImage = index;

            lightbox.style.display = "flex";

            showImage(currentImage);

        });

    });

}

const lightbox = document.getElementById("lightbox");

const lightboxImage = document.getElementById("lightbox-image");

const lightboxCaption = document.getElementById("lightbox-caption");

let currentImage = 0;

const previous = document.getElementById("previous");

const next = document.getElementById("next");

const close = document.querySelector(".close");


function showImage(index){

    lightboxImage.src = galleryImages[index].src;

    const caption = galleryImages[index].dataset.caption;

    if (caption) {
        lightboxCaption.textContent = caption;
        lightboxCaption.style.display = "block";
    }
    else {
        lightboxCaption.style.display = "none";
    }

}
galleryImages.forEach((image, index) => {

    image.addEventListener("click", () => {

        currentImage = index;

        lightbox.style.display = "flex";

        showImage(currentImage);

    });

});

previous.addEventListener("click", () => {
    currentImage--;

    if (currentImage < 0) {
        currentImage = galleryImages.length - 1;
    }

    showImage(currentImage);
});

next.addEventListener("click", () => {
    currentImage++;

    if (currentImage >= galleryImages.length) {
        currentImage = 0;
    }

    showImage(currentImage);
});

close.addEventListener("click", () => {

    lightbox.style.display = "none";

});

lightbox.addEventListener("click", (event) => {

    if (event.target === lightbox) {

        lightbox.style.display = "none";

    }

});

let touchStartX = 0;
let touchEndX = 0;

lightbox.addEventListener("touchstart", (event) => {
    touchStartX = event.changedTouches[0].screenX;
});

lightbox.addEventListener("touchend", (event) => {
    touchEndX = event.changedTouches[0].screenX;

    // Swipe Left
    if (touchStartX - touchEndX > 50) {
        next.click();
    }

    // Swipe Right
    if (touchEndX - touchStartX > 50) {
        previous.click();
    }
});

document.addEventListener("keydown", (event) => {

    if (lightbox.style.display !== "flex") {
        return;
    }

    if (event.key === "ArrowLeft") {
        previous.click();
    }

    if (event.key === "ArrowRight") {
        next.click();
    }

    if (event.key === "Escape") {
        close.click();
    }

});