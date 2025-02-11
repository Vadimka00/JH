document.addEventListener("DOMContentLoaded", function () {
    const commentText = document.getElementById("comment-text");
    const submitButton = document.querySelector(".btn-comment-submit");
    
    commentText.style.height = "40px";
    
    commentText.addEventListener("input", function () {
        this.style.height = "auto";
        this.style.height = this.scrollHeight + "px";
        const hasText = commentText.value.trim().length > 0;
        submitButton.disabled = !hasText;
    });
});
