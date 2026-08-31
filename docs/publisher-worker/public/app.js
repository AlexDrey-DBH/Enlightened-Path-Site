const loginShell = document.querySelector("#login-shell");
const appShell = document.querySelector("#app-shell");
const loginForm = document.querySelector("#login-form");
const loginMessage = document.querySelector("#login-message");
const postForm = document.querySelector("#post-form");
const formMessage = document.querySelector("#form-message");
const postsList = document.querySelector("#posts-list");
const refreshButton = document.querySelector("#refresh-button");
const logoutButton = document.querySelector("#logout-button");

function setMessage(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("error", isError);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  let payload = {};
  try {
    payload = await response.json();
  } catch {
    payload = { error: "The publisher returned an unreadable response." };
  }
  if (response.status === 401) {
    showLogin();
    throw new Error(payload.error || "Please sign in again.");
  }
  if (!response.ok) {
    throw new Error(payload.error || "The request could not be completed.");
  }
  return payload;
}

function showLogin() {
  appShell.hidden = true;
  loginShell.hidden = false;
}

function showApp() {
  loginShell.hidden = true;
  appShell.hidden = false;
}

function formatDate(value) {
  if (!value) return "No planned time";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function canPublish(post) {
  return post.status === "draft" && new Date(post.publishAt).getTime() <= Date.now();
}

function postItem(post) {
  const article = document.createElement("article");
  article.className = "post-item";

  const title = document.createElement("h3");
  title.textContent = post.title;
  article.append(title);

  const meta = document.createElement("p");
  meta.className = "post-meta";
  const status = document.createElement("span");
  status.className = "post-status";
  status.textContent = post.status;
  meta.append(status, document.createTextNode(` · ${formatDate(post.publishAt)}`));
  article.append(meta);

  if (post.status === "draft") {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = canPublish(post) ? "Publish Now" : "Not Ready Yet";
    button.disabled = !canPublish(post);
    button.addEventListener("click", () => publishDraft(post.slug, button));
    article.append(button);
  }
  return article;
}

async function loadPosts() {
  postsList.innerHTML = '<p class="empty-state">Loading posts...</p>';
  try {
    const { posts } = await api("/api/posts");
    postsList.replaceChildren();
    if (!posts.length) {
      postsList.innerHTML = '<p class="empty-state">No posts have been prepared here yet.</p>';
      return;
    }
    posts.forEach((post) => postsList.append(postItem(post)));
  } catch (error) {
    postsList.innerHTML = `<p class="message error"></p>`;
    postsList.querySelector("p").textContent = error.message;
  }
}

async function publishDraft(slug, button) {
  button.disabled = true;
  button.textContent = "Publishing...";
  try {
    await api(`/api/posts/${encodeURIComponent(slug)}/publish`, { method: "POST" });
    await loadPosts();
  } catch (error) {
    button.disabled = false;
    button.textContent = "Publish Now";
    window.alert(error.message);
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submit = loginForm.querySelector("button");
  submit.disabled = true;
  setMessage(loginMessage, "Signing in...");
  try {
    await api("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: loginForm.password.value }),
    });
    loginForm.reset();
    showApp();
    setMessage(loginMessage, "");
    await loadPosts();
  } catch (error) {
    setMessage(loginMessage, error.message, true);
  } finally {
    submit.disabled = false;
  }
});

postForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const action = event.submitter?.value || "draft";
  const buttons = postForm.querySelectorAll("button");
  buttons.forEach((button) => { button.disabled = true; });
  setMessage(formMessage, action === "publish" ? "Publishing..." : "Saving draft...");

  const data = new FormData(postForm);
  data.set("action", action);
  data.set("publishAt", new Date(postForm.publishAt.value).toISOString());

  try {
    const result = await api("/api/posts", { method: "POST", body: data });
    setMessage(formMessage, result.message);
    postForm.reset();
    await loadPosts();
  } catch (error) {
    setMessage(formMessage, error.message, true);
  } finally {
    buttons.forEach((button) => { button.disabled = false; });
  }
});

refreshButton.addEventListener("click", loadPosts);
logoutButton.addEventListener("click", async () => {
  await fetch("/api/logout", { method: "POST" });
  showLogin();
});

api("/api/session")
  .then(async () => {
    showApp();
    await loadPosts();
  })
  .catch(() => showLogin());
