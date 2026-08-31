const MAX_IMAGE_BYTES = 1024 * 1024;
const ALLOWED_IMAGE_TYPES = new Map([
  ["image/jpeg", "jpg"],
  ["image/png", "png"],
  ["image/webp", "webp"],
]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);
    }

    try {
      if (url.pathname === "/api/login" && request.method === "POST") {
        return login(request, env);
      }
      if (url.pathname === "/api/logout" && request.method === "POST") {
        return json({ ok: true }, 200, { "Set-Cookie": expiredCookie() });
      }
      if (!(await authorized(request, env))) {
        return json({ error: "Please sign in to continue." }, 401);
      }
      if (url.pathname === "/api/session" && request.method === "GET") {
        return json({ authenticated: true });
      }
      if (url.pathname === "/api/posts" && request.method === "GET") {
        const document = await readPosts(env);
        return json({ posts: sortPosts(document.posts) });
      }
      if (url.pathname === "/api/posts" && request.method === "POST") {
        return savePost(request, env);
      }
      const publishMatch = url.pathname.match(/^\/api\/posts\/([^/]+)\/publish$/);
      if (publishMatch && request.method === "POST") {
        return publishPost(decodeURIComponent(publishMatch[1]), env);
      }
      return json({ error: "Not found." }, 404);
    } catch (error) {
      console.error(error);
      return json({ error: error.message || "The publisher could not complete the request." }, 500);
    }
  },
};

async function login(request, env) {
  if (!env.PUBLISHER_PASSWORD) {
    return json({ error: "The publisher password has not been configured." }, 503);
  }
  const body = await request.json().catch(() => ({}));
  if (!timingSafeEqual(String(body.password || ""), env.PUBLISHER_PASSWORD)) {
    return json({ error: "That password is not correct." }, 401);
  }
  return json(
    { authenticated: true },
    200,
    { "Set-Cookie": await sessionCookie(env.PUBLISHER_PASSWORD) },
  );
}

async function authorized(request, env) {
  if (!env.PUBLISHER_PASSWORD) return false;
  const cookie = request.headers.get("Cookie") || "";
  const match = cookie.match(/(?:^|;\s*)eph_publisher=([^;]+)/);
  if (!match) return false;
  const expected = await sessionToken(env.PUBLISHER_PASSWORD);
  return timingSafeEqual(match[1], expected);
}

async function sessionToken(password) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode("enlightened-path-publisher-session-v1"),
  );
  return base64Url(new Uint8Array(signature));
}

async function sessionCookie(password) {
  const token = await sessionToken(password);
  return `eph_publisher=${token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=43200`;
}

function expiredCookie() {
  return "eph_publisher=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0";
}

async function savePost(request, env) {
  const form = await request.formData();
  const title = clean(form.get("title"), 180);
  const body = clean(form.get("body"), 30000);
  const topic = clean(form.get("topic"), 80);
  const imageAlt = clean(form.get("imageAlt"), 220);
  const action = form.get("action") === "publish" ? "publish" : "draft";
  const publishAt = validDate(form.get("publishAt"));
  const image = form.get("image");

  if (!title || !body || !imageAlt || !publishAt || !TOPICS[topic]) {
    return json({ error: "Complete every required field before saving." }, 400);
  }
  if (!(image instanceof File) || !image.size || !ALLOWED_IMAGE_TYPES.has(image.type)) {
    return json({ error: "Choose a JPG, PNG, or WebP featured image." }, 400);
  }
  if (image.size > MAX_IMAGE_BYTES) {
    return json({ error: "The featured image must be 1 MB or smaller for the free publisher." }, 400);
  }
  if (action === "publish" && new Date(publishAt).getTime() > Date.now()) {
    return json({ error: "Save this as a draft, then return at the planned time to publish it." }, 400);
  }

  const document = await readPosts(env);
  const slug = uniqueSlug(slugify(title), document.posts);
  const extension = ALLOWED_IMAGE_TYPES.get(image.type);
  const imagePath = `assets/blog/${slug}/hero.${extension}`;
  const now = new Date().toISOString();
  const post = {
    id: crypto.randomUUID(),
    slug,
    title,
    body,
    topic,
    publishAt,
    status: action === "publish" ? "published" : "draft",
    imagePath,
    imageAlt,
    createdAt: now,
    publishedAt: action === "publish" ? now : null,
  };

  await putRepositoryFile(
    env,
    imagePath,
    bytesToBase64(new Uint8Array(await image.arrayBuffer())),
    `Add image for blog draft: ${title}`,
  );
  document.posts.push(post);
  await writePosts(env, document, `Save blog ${action}: ${title}`);

  return json({
    post,
    message: action === "publish"
      ? "Published. GitHub Pages is now building the article and updating the blog."
      : "Draft saved. Return at the planned time and choose Publish Now.",
  }, 201);
}

async function publishPost(slug, env) {
  const document = await readPosts(env);
  const post = document.posts.find((item) => item.slug === slug);
  if (!post) return json({ error: "That draft could not be found." }, 404);
  if (post.status === "published") return json({ post, message: "This post is already published." });
  if (new Date(post.publishAt).getTime() > Date.now()) {
    return json({ error: "This post cannot be published before its planned time." }, 400);
  }
  post.status = "published";
  post.publishedAt = new Date().toISOString();
  await writePosts(env, document, `Publish blog post: ${post.title}`);
  return json({ post, message: "Published. GitHub Pages is now updating the website." });
}

async function readPosts(env) {
  const response = await githubRequest(env, `contents/${env.CONTENT_PATH}`);
  if (response.status === 404) return { posts: [], sha: null };
  const payload = await githubJson(response, "The publisher could not read its post list.");
  const parsed = JSON.parse(new TextDecoder().decode(base64ToBytes(payload.content.replace(/\s/g, ""))));
  return { posts: Array.isArray(parsed.posts) ? parsed.posts : [], sha: payload.sha };
}

async function writePosts(env, document, message) {
  const payload = {
    message,
    content: bytesToBase64(new TextEncoder().encode(`${JSON.stringify({ posts: document.posts }, null, 2)}\n`)),
    branch: "main",
  };
  if (document.sha) payload.sha = document.sha;
  const response = await githubRequest(env, `contents/${env.CONTENT_PATH}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  await githubJson(response, "The publisher could not update its post list.");
}

async function putRepositoryFile(env, path, content, message) {
  const current = await githubRequest(env, `contents/${path}`);
  const payload = { message, content, branch: "main" };
  if (current.ok) payload.sha = (await current.json()).sha;
  const response = await githubRequest(env, `contents/${path}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  await githubJson(response, "The publisher could not save the featured image.");
}

function githubRequest(env, path, options = {}) {
  if (!env.GITHUB_TOKEN) throw new Error("The GitHub token has not been configured.");
  return fetch(`https://api.github.com/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/${path}`, {
    ...options,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "enlightened-path-blog-publisher",
      "X-GitHub-Api-Version": "2026-03-10",
      ...(options.headers || {}),
    },
  });
}

async function githubJson(response, fallback) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.message ? `${fallback} GitHub: ${payload.message}` : fallback);
  }
  return payload;
}

function validDate(value) {
  const date = new Date(String(value || ""));
  return Number.isNaN(date.getTime()) ? "" : date.toISOString();
}

function clean(value, limit) {
  return String(value || "").replace(/\r\n/g, "\n").trim().slice(0, limit);
}

function slugify(value) {
  return value.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 100) || "blog-post";
}

function uniqueSlug(base, posts) {
  const used = new Set(posts.map((post) => post.slug));
  if (!used.has(base)) return base;
  let suffix = 2;
  while (used.has(`${base}-${suffix}`)) suffix += 1;
  return `${base}-${suffix}`;
}

function sortPosts(posts) {
  return [...posts].sort((a, b) => String(b.publishAt).localeCompare(String(a.publishAt)));
}

function timingSafeEqual(left, right) {
  const a = new TextEncoder().encode(left);
  const b = new TextEncoder().encode(right);
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let index = 0; index < a.length; index += 1) difference |= a[index] ^ b[index];
  return difference === 0;
}

function bytesToBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let index = 0; index < bytes.length; index += chunk) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunk));
  }
  return btoa(binary);
}

function base64ToBytes(value) {
  return Uint8Array.from(atob(value), (character) => character.charCodeAt(0));
}

function base64Url(bytes) {
  return bytesToBase64(bytes).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function json(payload, status = 200, headers = {}) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
      "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
      ...headers,
    },
  });
}

const TOPICS = {
  "healing-spiritual-growth": "Healing & Spiritual Growth",
  "reiki-energy-healing": "Reiki & Energy Healing",
  "akashic-records-intuition": "Akashic Records & Intuition",
  "meditation-mindfulness": "Meditation & Mindfulness",
  "work-burnout-everyday-life": "Work, Burnout & Everyday Life",
  "astrology-guest-posts": "Astrology & Guest Posts",
};
