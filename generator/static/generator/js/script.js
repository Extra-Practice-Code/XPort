// Get the modal
const modal = document.getElementById("modalbox");

const modalTitle = document.getElementById("modal--gallery-title");

const modalCounter = document.getElementsByClassName("modal--counter")[0];
const modalContent = document.getElementsByClassName("modal--content")[0];
const modalImg = document.getElementById("modal--image");
const modalVideo = document.getElementById("modal--video");
let modalVideoImg;
let modalVideoLink;
const authorText = document.getElementById("modal--image-author");
const titleText = document.getElementById("modal--image-title");
const captionText = document.getElementById("modal--image-caption");

const closeBtn = document.getElementsByClassName("close")[0];
const leftBtn = document.getElementsByClassName("leftArrow")[0];
const rightBtn = document.getElementsByClassName("rightArrow")[0];

let galleryTitle = '';
let galleryArray = [];
let itemImgArray = [];
let inlineArray = [];
let imageType = "none";
let imgIndex = 0;

const setModalTitle = (input) => {
    modalTitle.innerHTML = input
}
const setImage = (input) => {
    if (modalImg.style.display == "none") {
        modalImg.style.display = "block"
        modalVideo.style.display = "none"
    }
    modalImg.src = input.srcFull;
};

const setVideo = (input) => {
    console.log(input)
    modalVideoLink.href = `https://www.youtube-nocookie.com/embed/${input.videoSrc}?autoplay=1`
    modalVideoImg.src = `http://img.youtube.com/vi/${input.videoSrc}/maxresdefault.jpg`
    modalVideo.style.display = "block";
    modalImg.style.display = "none";
}

const setAuthor = (input) => {
    if (input.author != "None" && input.author != "") {
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
    modalVideoImg = document.getElementById('modal--video').contentWindow.document.getElementById('modal--video-img')
    modalVideoLink = document.getElementById('modal--video').contentWindow.document.getElementById('modal--video-link')

    

    if (imageType == 'gallery') {
        imageArray = galleryArray;
    } else if(imageType == 'itemImage'){
        imageArray = itemImgArray;
    } else if (imageType == 'inlineImage') {
        imageArray = inlineArray;
    }


    modal.style.display = "grid";
    modalCounter.innerHTML = `${imgIndex + 1} / ${array.length}`;

    setModalTitle(galleryTitle);
    updateModal(array[startingIndex], startingIndex);

    if (array.length > 1) {
        leftBtn.style.visibility = "visible";
        rightBtn.style.visibility = "visible";
    }
};

const updateModal = (input, idx) => {
    modalCounter.innerHTML = `${idx + 1} / ${imageArray.length}`;
    if (input.contentType != 'video') {
        setImage(input)
    } else {
        setVideo(input)
    }
    setAuthor(input)
    setTitle(input)
    setCaption(input)
}

const wrappedModulus = (a, b) => ((a % b) + b) % b; //Helper function to wrap around the array

const prevImg = () => {
    imgIndex = wrappedModulus(imgIndex - 1, imageArray.length);
    updateModal(imageArray[imgIndex], imgIndex)
};

const nextImg = () => {
    imgIndex = (imgIndex + 1) % imageArray.length;
    updateModal(imageArray[imgIndex], imgIndex)
};

const closeModal = () => {
    if (modal.style.display != "none") {
        modal.style.display = "none";
        imgIndex = 0;
        galleryTitle = "";
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
const itemImages = document.querySelectorAll(
    ".item--reference.item-type--image"
)

const inlineImages = document.querySelectorAll(".inline-image");

galleries.forEach((gallery) => {
    gallery.addEventListener("click", (element) => {
        galleryTitle = gallery.querySelector('.item--gallery-description').children[0].innerHTML;
        galleryImage = gallery.querySelectorAll(".item--image");
        galleryArray = [];
        galleryImage.forEach((img) => {
            galleryArray.push(img.dataset);
        });
        imageType = "gallery";
        displayModal(galleryArray, 0);
    });
});

itemImages.forEach((itemImg) => {
    itemImgData = itemImg.querySelectorAll(".item--image")[0].dataset
    itemImgArray.push(itemImgData)
    itemImg.addEventListener("click", (element) => {
        imageType = "itemImage";
        imgIndex = itemImgArray.findIndex((idx) => element.target.dataset == idx);
        displayModal(itemImgArray, imgIndex)
    })
})

inlineImages.forEach((inlineImage) => {
    inlineArray.push(inlineImage.dataset);

    inlineImage.addEventListener("click", (element) => {
        imageType = "inlineImage";
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
