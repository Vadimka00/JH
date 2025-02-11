const likeButtons = document.querySelectorAll('.interaction-btn');

likeButtons.forEach(button => {
    button.addEventListener('click', function(event) {
        const postOwner = button.getAttribute('data-post-owner');
        const postId = button.getAttribute('data-post-id');

        fetch('/like', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_owner: postOwner,
                post_id: postId,
            })
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    alert('Пожалуйста, авторизуйтесь, чтобы поставить лайк');
                    window.location.href = '/login';
                }
                throw new Error('User not authorized');
            }
            return response.json();
        })
        .then(data => {
            const likeCountSpan = button.querySelector('span');
            likeCountSpan.textContent = data.likeCount;

            if (data.liked) {
                button.classList.add('liked');
            } else {
                button.classList.remove('liked');
            }

            console.log(`Пост с ID: ${postId} был лайкнут/дислайкнут пользователем ${postOwner}. Новое количество лайков: ${data.likeCount}`);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const likeButtons = document.querySelectorAll('.interaction-btn');

    likeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const postId = this.getAttribute('data-post-id');
            const isLiked = this.classList.contains('liked');

            fetch('/like', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    post_id: postId,
                    post_owner: this.closest('.post').querySelector('.user-login').textContent,
                })
            })
            .then(response => response.json())
            .then(data => {
                this.nextElementSibling.textContent = `${data.likeCount} лайков`;

                if (isLiked) {
                    this.classList.remove('liked');
                } else {
                    this.classList.add('liked');
                }
            })
            .catch(error => {
                console.error('Ошибка при изменении лайка:', error);
            });
        });
    });
});
