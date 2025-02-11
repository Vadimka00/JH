document.addEventListener("DOMContentLoaded", function () {
    const postForm = document.getElementById("post-form");
    const postText = document.getElementById("post-text");
    const postImage = document.getElementById("post-image");
    const submitButton = document.querySelector(".btn-submit");
    const attachButton = document.querySelector(".btn-attach");
    const previewContainer = document.createElement("div");
    previewContainer.style.width = "100%";
    previewContainer.style.textAlign = "center";
    previewContainer.style.marginBottom = "10px";
    previewContainer.style.position = "relative";
    
    postForm.insertBefore(previewContainer, postForm.firstChild);

    function updateButtonState() {
        const hasText = postText.value.trim().length > 0;
        const hasImage = postImage.files.length > 0;
        submitButton.disabled = !(hasText && hasImage);
    }
    
    function previewImage() {
        previewContainer.innerHTML = "";
        if (postImage.files.length > 0) {
            const file = postImage.files[0];
            const reader = new FileReader();
            reader.onload = function (e) {
                const blurredBg = document.createElement("img");
                blurredBg.src = e.target.result;
                blurredBg.style.position = "absolute";
                blurredBg.style.top = "0";
                blurredBg.style.left = "0";
                blurredBg.style.width = "100%";
                blurredBg.style.height = "100%";
                blurredBg.style.borderRadius = "10px";
                blurredBg.style.objectFit = "cover";
                blurredBg.style.filter = "blur(5px)";
                blurredBg.style.opacity = "1";

                const img = document.createElement("img");
                img.src = e.target.result;
                img.style.maxWidth = "100%";
                img.style.borderRadius = "10px";
                img.style.position = "relative";
                img.style.zIndex = "1";
                img.style.marginBottom = "5px";

                previewContainer.appendChild(blurredBg);
                previewContainer.appendChild(img);
                attachButton.style.background = "#e0b700";
                attachButton.style.minWidth = "140px";
                attachButton.textContent = "Изменить фото";
            };
            reader.readAsDataURL(file);
        } else {
            attachButton.style.background = "#388E3C";
        }
        updateButtonState();
    }

    postText.style.height = "40px";
    postText.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";
        updateButtonState();
    });

    postImage.addEventListener("change", previewImage);
    postText.addEventListener("input", updateButtonState);

    postForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const formData = new FormData();
        formData.append("user_login", userLogin);
        formData.append("text", postText.value);
        if (postImage.files.length > 0) {
            formData.append("image", postImage.files[0]);
        }

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.message === "Пост успешно загружен") {
                location.reload();
                updateButtonState();
            } else {
                alert("Произошла ошибка при отправке поста");
            }
        })
        .catch(error => {
            console.error("Ошибка:", error);
            alert("Произошла ошибка при отправке поста");
        });
    });

    updateButtonState();
});


document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', function() {
        const postId = this.getAttribute('data-post-id');
        const userLogin = this.getAttribute('data-login');

        fetch('/delete_post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_id: postId,
                user_login: userLogin
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Ошибка при удалении публикации');
            }
        })
        .catch(error => console.error('Ошибка:', error));
    });
});

const modal = document.getElementById('edit-profile-modal');
const editBtn = document.getElementById('edit-profile-btn');
const closeModal = document.getElementById('close-modal');

editBtn.onclick = function() {
    fetch(`/edit-profile/${userLogin}`)
        .then(response => response.json())
        .then(data => {
            const user = data.user;
            document.getElementById('first-name').value = user.name;
            document.getElementById('last-name').value = user.surname;
            document.getElementById('city').value = user.city;
            document.getElementById('birth-date').value = user.birth;
            document.getElementById('about-me').value = user.bio;
            
            modal.style.display = "flex";
        })
        .catch(error => console.error('Error fetching user data:', error));
}

closeModal.onclick = function() {
    modal.style.display = "none";
}

window.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
}

document.querySelector('.profile-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(this);
    fetch(`/edit-profile/${userLogin}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        location.reload();
        modal.style.display = "none";
    })
    .catch(error => console.error('Error updating profile:', error));
});
