document.addEventListener("DOMContentLoaded", function () {
    // Image upload functionality
    const uploadForm = document.getElementById("uploadForm");

    if (uploadForm) {
        uploadForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const files = uploadForm.querySelector('input[type="file"]').files;
            const formData = new FormData();
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

            for (const file of files) {
                formData.append("image", file);
            }
            formData.append("csrf_token", csrfToken); // Append CSRF token to formData

            fetch("/upload", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": csrfToken // Include CSRF token in the headers if needed
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    data.urls.forEach(url => addImageToGallery(url, url.split('/').pop()));
                } else {
                    alert("Error uploading images.");
                }
            })
            .catch(error => console.error("Error:", error));
        });
    }

    function addImageToGallery(imageUrl, filename) {
        const gallery = document.getElementById("gallery");
        const imageCard = document.createElement("div");
        imageCard.classList.add("image-card");
        imageCard.setAttribute("data-filename", filename);

        const img = document.createElement("img");
        img.src = imageUrl;
        img.alt = filename;

        const imageInfo = document.createElement("div");
        imageInfo.classList.add("image-info");

        const imageTitle = document.createElement("h3");
        imageTitle.classList.add("image-title");
        imageTitle.textContent = filename;

        const deleteButton = document.createElement("button");
        deleteButton.classList.add("delete-button");
        deleteButton.textContent = "Delete";

        const copyLinkButton = document.createElement("button");
        copyLinkButton.classList.add("copy-link-button");
        copyLinkButton.textContent = "Copy Link";
        copyLinkButton.setAttribute("data-url", imageUrl);

        imageInfo.appendChild(imageTitle);
        imageCard.appendChild(img);
        imageCard.appendChild(imageInfo);
        imageCard.appendChild(deleteButton);
        imageCard.appendChild(copyLinkButton);
        gallery.prepend(imageCard); // Add new images to the top of the gallery
    }

    document.getElementById("gallery").addEventListener("click", function (event) {
        if (event.target.classList.contains("delete-button")) {
            const imageCard = event.target.closest(".image-card");
            const filename = imageCard.getAttribute("data-filename");

            if (confirm(`Are you sure you want to delete '${filename}'?`)) {
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                fetch(`/delete/${filename}`, {
                    method: "DELETE",
                    headers: {
                        "X-CSRFToken": csrfToken
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        return response.text().then(text => { throw new Error(text); });
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        imageCard.remove();
                    } else {
                        alert("Error deleting image.");
                    }
                })
                .catch(error => console.error("Error:", error));
            }
        }

        if (event.target.classList.contains("copy-link-button")) {
            const url = event.target.getAttribute("data-url");
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(() => {
                    alert('Image link copied to clipboard!');
                }).catch(err => {
                    console.error('Error copying link: ', err);
                });
            } else {
                alert('Clipboard API not supported or not accessible.');
            }
        }
    });

    // Signup functionality
    const signupForm = document.getElementById("signup-form");

    if (signupForm) {
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const formData = new FormData(signupForm);

            fetch(signupForm.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": formData.get('csrf_token')
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => { throw new Error(text); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.href = data.redirect || '/login';
                } else {
                    alert(data.message || "Error signing up.");
                }
            })
            .catch(error => console.error("Error:", error));
        });
    }
});

