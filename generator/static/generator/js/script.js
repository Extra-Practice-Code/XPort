// Get the modal
const modal = document.getElementById("modalbox");
const modalImg = document.getElementById("modalImage");
const captionText = document.getElementById("modalCaption");
const closeBtn = document.getElementsByClassName("close")[0];
const leftBtn = document.getElementsByClassName('leftArrow')[0];
const rightBtn = document.getElementsByClassName('rightArrow')[0];

let imageArray = []
let imgIndex = 0;

document.querySelectorAll('.item--gallery--image').forEach(element => {
    imageArray.push(element.dataset)
    
    element.addEventListener('click', (ele) => {
        imgIndex = imageArray.findIndex(idx => ele.target.dataset == idx)
        console.log(imgIndex)
        modal.style.display = "flex";
        modalImg.src = element.dataset.srcFull;
        captionText.innerHTML = element.dataset.author
    })

});

if (imageArray.length > 1) {
    leftBtn.style.display = "flex";
    rightBtn.style.display = "flex";
}

console.log(imageArray.length > 1)

window.onkeydown = (e) => {
    if (e.key == "Escape"){
        closeModal()
    }
    if (e.key == "ArrowLeft"){
        prevImg()
    }
    if (e.key == "ArrowRight"){
        nextImg()
    }
}

const closeModal = () => {
    if (modal.style.display != "none"){
        modal.style.display = "none"
    }
}

const prevImg = () => {
    if (imgIndex != 0){
        imgIndex -= 1;
        modalImg.src = imageArray[imgIndex].srcFull;
        captionText.innerHTML = imageArray[imgIndex].author;

    } else {
        imgIndex = imageArray.length-1
        modalImg.src = imageArray[imgIndex].srcFull;
        captionText.innerHTML = imageArray[imgIndex].author;

    }
}
const nextImg = () => {
    imgIndex = (imgIndex + 1) % imageArray.length;
    modalImg.src = imageArray[imgIndex].srcFull;
    captionText.innerHTML = imageArray[imgIndex].author;
}

closeBtn.onclick = closeModal
leftBtn.onclick = prevImg
rightBtn.onclick = nextImg