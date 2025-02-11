document.addEventListener("DOMContentLoaded", function () {
    const commentForm = document.getElementById("comment-form");
    const commentText = document.getElementById("comment-text");
    const commentButton = document.querySelector('.interaction-btn-comments');
    const submitButton = commentForm.querySelector(".btn-comment-submit");

    commentText.addEventListener("input", function () {
        submitButton.disabled = commentText.value.trim() === "";
    });

    commentForm.addEventListener("submit", function (e) {
        e.preventDefault();

        const comment = commentText.value.trim();
        if (!comment) return;

        const postOwner = commentForm.dataset.postOwner;
        const postId = commentForm.dataset.postId;

        fetch("/add_comment", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                post_owner: postOwner,
                post_id: postId,
                comment_text: comment
            })
        })
        .then(response => response.json())
        .then(data => {
            const commentCountSpan = commentButton.querySelector('span');
            if (commentCountSpan) {
                commentCountSpan.textContent = data.CommentCount;
            }
            submitButton.disabled = true;
            window.location.reload();

            if (data.CommentCount > 0) {
                commentButton.classList.add('commented');
            }
        })
        .catch(error => console.error("Error:", error));
    });
});
