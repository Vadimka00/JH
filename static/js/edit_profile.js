document.addEventListener("DOMContentLoaded", function () {
    const avatarInput = document.getElementById("avatar");
    const avatarPreview = document.getElementById("avatar-preview");
    const aboutMe = document.getElementById("about-me");
    const charCount = document.getElementById("char-count");

    avatarInput.addEventListener("change", function (event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                avatarPreview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    });

    aboutMe.style.height = "140px"
    aboutMe.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";

        const currentLength = this.value.length;
        const maxLength = 200;
        const remainingChars = maxLength - currentLength;

        charCount.textContent = `${currentLength}/${maxLength} символов`;

        if (remainingChars === 0) {
            charCount.style.color = "red";
        } else if (remainingChars <= 20) {
            charCount.style.color = "orange";
        } else {
            charCount.style.color = "green";
        }

        if (currentLength > 200) {
            aboutMe.value = aboutMe.value.substring(0, 200);
        }
    });

    (function initializeCharacterCount() {
        const currentLength = aboutMe.value.length;
        const maxLength = 200;
        const remainingChars = maxLength - currentLength;

        charCount.textContent = `${currentLength}/${maxLength} символов`;

        if (remainingChars === 0) {
            charCount.style.color = "red";
        } else if (remainingChars <= 20) {
            charCount.style.color = "orange";
        } else {
            charCount.style.color = "green";
        }
    })();
});

document.addEventListener('DOMContentLoaded', function () {
    flatpickr("#birth-date", {
        dateFormat: "d/m/Y",
        locale: "ru",
        minDate: "01-01-1900",
        maxDate: "today",
        disableMobile: true,
        theme: "light",
        onOpen: function() {
            const prevArrow = document.querySelector('.flatpickr-prev-month');
            const nextArrow = document.querySelector('.flatpickr-next-month');
            if (prevArrow) prevArrow.style.color = '#388E3C';
            if (nextArrow) nextArrow.style.color = '#388E3C';
        }
    });
});