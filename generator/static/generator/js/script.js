// Get the modal
const modal = document.getElementById("modalbox");

const modalTitle = document.getElementById("modal--gallery-title");

const modalCounter = document.getElementsByClassName("modal--counter")[0];
const modalImg = document.getElementById("modal--image");

const authorText = document.getElementById("modal--image-author");
const titleText = document.getElementById("modal--image-title");
const captionText = document.getElementById("modal--image-caption");

const closeBtn = document.getElementsByClassName("close")[0];
const leftBtn = document.getElementsByClassName("leftArrow")[0];
const rightBtn = document.getElementsByClassName("rightArrow")[0];

let galleryTitle = '';
let galleryArray = [];
let inlineArray = [];
let isGallery = false;
let imgIndex = 0;

const setModalTitle = (input) => {
    modalTitle.innerHTML = input
}
const setImage = (input) => {
    modalImg.src = input.srcFull;
};

const setAuthor = (input) => {
    if (input.author != "None") {
        authorText.innerHTML = `By ${input.author}`;
    }
};
const setTitle = (input) => {
    if (input.title != "None") {
        titleText.innerHTML = input.title;
    }
};

const setCaption = (input) => {
    if (input.caption != "None") {
        captionText.innerHTML = input.caption;
    }
};

const displayModal = (array, startingIndex) => {
    modal.style.display = "grid";
    modalCounter.innerHTML = `${imgIndex + 1} / ${array.length}`;

    setModalTitle(galleryTitle);
    setImage(array[startingIndex]);
    setAuthor(array[startingIndex]);
    setTitle(array[startingIndex]);
    setCaption(array[startingIndex]);

    if (array.length > 1) {
        leftBtn.style.visibility = "visible";
        rightBtn.style.visibility = "visible";
    }
};

const wrappedModulus = (a, b) => ((a % b) + b) % b; //Helper function to wrap around the array

const prevImg = () => {
    if (isGallery) {
        let imageArray = galleryArray;
    } else {
        let imageArray = inlineArray;
    }

    imgIndex = wrappedModulus(imgIndex - 1, imageArray.length);
    modalCounter.innerHTML = `${imgIndex + 1} / ${imageArray.length}`;

    setImage(imageArray[imgIndex]);
    setAuthor(imageArray[imgIndex]);
    setTitle(imageArray[imgIndex]);
    setCaption(imageArray[imgIndex]);
};

const nextImg = () => {
    if (isGallery) {
        imageArray = galleryArray;
    } else {
        imageArray = inlineArray;
    }

    imgIndex = (imgIndex + 1) % imageArray.length;
    modalCounter.innerHTML = `${imgIndex + 1} / ${imageArray.length}`;

    setImage(imageArray[imgIndex]);
    setAuthor(imageArray[imgIndex]);
    setTitle(imageArray[imgIndex]);
    setCaption(imageArray[imgIndex]);
};

const closeModal = () => {
    if (modal.style.display != "none") {
        modal.style.display = "none";
        imgIndex = 0;
        modalTitle.innerHTML = "";
        authorText.innerHTML = "";
        titleText.innerHTML = "";
        captionText.innerHTML = "";
        modalImg.src = "";
        leftBtn.style.visibility = "hidden";
        rightBtn.style.visibility = "hidden";
    }
};

const galleries = document.querySelectorAll(
    ".item--reference.item-type--gallery"
);
const inlineImages = document.querySelectorAll(".inline-image");

galleries.forEach((gallery) => {
    gallery.addEventListener("click", (element) => {
        galleryTitle = gallery.querySelector('.item--description').textContent
        galleryImage = gallery.querySelectorAll(".item--image");
        galleryArray = [];
        galleryImage.forEach((img) => {
            galleryArray.push(img.dataset);
        });
        isGallery = true;
        displayModal(galleryArray, 0);
    });
});

inlineImages.forEach((inlineImage) => {
    inlineArray.push(inlineImage.dataset);

    inlineImage.addEventListener("click", (element) => {
        isGallery = false;
        imgIndex = inlineArray.findIndex((idx) => element.target.dataset == idx);
        displayModal(inlineArray, imgIndex);
    });
});

window.onkeydown = (e) => {
    if (e.key == "Escape") {
        closeModal();
    }
    if (e.key == "ArrowLeft") {
        prevImg();
    }
    if (e.key == "ArrowRight") {
        nextImg();
    }
};

closeBtn.onclick = closeModal;
leftBtn.onclick = prevImg;
rightBtn.onclick = nextImg;
