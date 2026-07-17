(() => {
  const collapsedClass = "nav-collapsed";
  const menuOpenClass = "mobile-menu-open";
  const mobileQuery = window.matchMedia("(max-width: 720px)");
  const header = document.querySelector(".site-header");
  const nav = document.querySelector(".site-header .nav");
  const logoLink = document.querySelector(".site-header .nav > a");
  const navLinks = document.querySelector(".site-header .nav-links");
  const navButton = document.querySelector(".site-header .nav-links .button");
  const fullButtonLabel = navButton ? navButton.textContent.trim() : "";
  let menuButton = document.querySelector(".site-header .nav-toggle");
  let isCollapsed = false;
  let isMenuOpen = false;

  if (navButton && fullButtonLabel) {
    navButton.setAttribute("aria-label", fullButtonLabel);
  }

  if (nav && logoLink && navLinks) {
    if (!menuButton) {
      menuButton = document.createElement("button");
      menuButton.className = "nav-toggle";
      menuButton.type = "button";
      menuButton.innerHTML = "<span></span><span></span><span></span>";
      nav.insertBefore(menuButton, navLinks);
    }
    menuButton.setAttribute("aria-label", "Open navigation menu");
    menuButton.setAttribute("aria-expanded", "false");
  }

  function setMenuOpen(nextOpen) {
    isMenuOpen = Boolean(nextOpen && mobileQuery.matches);
    document.body.classList.toggle(menuOpenClass, isMenuOpen);
    if (menuButton) {
      menuButton.setAttribute("aria-expanded", isMenuOpen ? "true" : "false");
      menuButton.setAttribute("aria-label", isMenuOpen ? "Close navigation menu" : "Open navigation menu");
    }
    if (navButton && fullButtonLabel) {
      navButton.textContent = isCollapsed && !isMenuOpen ? "Book" : fullButtonLabel;
    }
    window.requestAnimationFrame(syncHeaderSpace);
    window.setTimeout(syncHeaderSpace, 260);
  }

  function syncHeaderSpace() {
    if (!header || !mobileQuery.matches || (isCollapsed && !isMenuOpen)) return;
    document.documentElement.style.setProperty(
      "--mobile-header-space",
      `${Math.ceil(header.offsetHeight)}px`
    );
  }

  function updateMobileNav() {
    syncHeaderSpace();

    if (!mobileQuery.matches) {
      isCollapsed = false;
      setMenuOpen(false);
      document.body.classList.remove(collapsedClass);
      document.documentElement.style.removeProperty("--mobile-header-space");
    } else if (!isCollapsed && window.scrollY > 260) {
      isCollapsed = true;
      document.body.classList.add(collapsedClass);
    } else if (isCollapsed && window.scrollY < 80) {
      isCollapsed = false;
      document.body.classList.remove(collapsedClass);
    }

    if (navButton && fullButtonLabel) {
      navButton.textContent = isCollapsed && !isMenuOpen ? "Book" : fullButtonLabel;
    }
  }

  menuButton.addEventListener("click", () => setMenuOpen(!isMenuOpen));
  navLinks?.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => setMenuOpen(false));
  });
  window.addEventListener("load", updateMobileNav);
  window.addEventListener("scroll", updateMobileNav, { passive: true });
  window.addEventListener("resize", () => {
    if (mobileQuery.matches && isCollapsed) return;
    updateMobileNav();
  });
  mobileQuery.addEventListener("change", updateMobileNav);
  updateMobileNav();
})();

(() => {
  const carousel = document.querySelector("[data-carousel]");
  if (!carousel) return;

  const track = carousel.querySelector("[data-carousel-track]");
  const slides = Array.from(carousel.querySelectorAll(".carousel-slide"));
  const previousButton = carousel.querySelector("[data-carousel-prev]");
  const nextButton = carousel.querySelector("[data-carousel-next]");
  const dotsWrap = carousel.querySelector("[data-carousel-dots]");
  let activeIndex = 0;
  let scrollFrame = null;

  if (!track || slides.length === 0 || !dotsWrap) return;

  const dots = slides.map((_, index) => {
    const dot = document.createElement("button");
    dot.className = "carousel-dot";
    dot.type = "button";
    dot.setAttribute("aria-label", `Show reflection ${index + 1}`);
    dot.addEventListener("click", () => goToSlide(index));
    dotsWrap.appendChild(dot);
    return dot;
  });

  function updateDots(index) {
    activeIndex = index;
    dots.forEach((dot, dotIndex) => {
      dot.setAttribute("aria-current", dotIndex === activeIndex ? "true" : "false");
    });
  }

  function nearestSlideIndex() {
    const trackLeft = track.scrollLeft;
    return slides.reduce((nearest, slide, index) => {
      const distance = Math.abs(slide.offsetLeft - track.offsetLeft - trackLeft);
      return distance < nearest.distance ? { index, distance } : nearest;
    }, { index: 0, distance: Number.POSITIVE_INFINITY }).index;
  }

  function goToSlide(index) {
    const nextIndex = (index + slides.length) % slides.length;
    const slide = slides[nextIndex];
    track.scrollTo({
      left: slide.offsetLeft - track.offsetLeft,
      behavior: "smooth"
    });
    updateDots(nextIndex);
  }

  previousButton?.addEventListener("click", () => goToSlide(activeIndex - 1));
  nextButton?.addEventListener("click", () => goToSlide(activeIndex + 1));
  track.addEventListener("scroll", () => {
    if (scrollFrame) return;
    scrollFrame = window.requestAnimationFrame(() => {
      updateDots(nearestSlideIndex());
      scrollFrame = null;
    });
  }, { passive: true });

  updateDots(0);
})();

(() => {
  const forms = Array.from(document.querySelectorAll("[data-discovery-form]"));
  if (!forms.length) return;

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function setStatus(form, message, isError = false) {
    const status = form.querySelector("[data-discovery-status]");
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  }

  function endpointFor(form) {
    const endpoint = form.dataset.sheetEndpoint || window.EPH_DISCOVERY_SHEET_ENDPOINT || "";
    return endpoint.trim();
  }

  function buildPayload(form, emailInput) {
    const firstNameInput = form.querySelector('[name="firstName"]');
    const inquiryInput = form.querySelector('[name="inquiryType"]');
    const messageInput = form.querySelector('[name="message"]');
    const newsletterInput = form.querySelector('[name="newsletterOptIn"]');
    return {
      submittedAt: new Date().toISOString(),
      formName: form.dataset.formName || "Discovery Call Request",
      source: form.dataset.formSource || "contact",
      firstName: firstNameInput?.value.trim() || "",
      email: emailInput.value.trim(),
      inquiryType: inquiryInput?.value || "",
      message: messageInput?.value.trim() || "",
      newsletterOptIn: newsletterInput?.checked ? "yes" : "no",
      pageUrl: window.location.href,
      pageTitle: document.title,
      userAgent: navigator.userAgent
    };
  }

  async function submitToSheet(form, payload) {
    const endpoint = endpointFor(form);
    if (!endpoint) {
      throw new Error("Discovery form endpoint is not configured.");
    }

    await fetch(endpoint, {
      method: "POST",
      mode: "no-cors",
      headers: {
        "Content-Type": "text/plain;charset=utf-8"
      },
      body: JSON.stringify(payload)
    });
    return "sheet";
  }

  forms.forEach((form) => {
    const emailInput = form.querySelector('input[type="email"]');
    const firstNameInput = form.querySelector('[name="firstName"]');
    const inquiryInput = form.querySelector('[name="inquiryType"]');
    const button = form.querySelector('button[type="submit"]');
    const initialButtonText = button ? button.textContent.trim() : "Send";

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!emailInput || !firstNameInput || !inquiryInput || !button) return;

      const trap = form.querySelector('[name="website"]');
      if (trap && trap.value.trim()) {
        form.reset();
        setStatus(form, "Thank you. Your request has been received.");
        return;
      }

      firstNameInput.setAttribute("aria-invalid", firstNameInput.value.trim() ? "false" : "true");
      inquiryInput.setAttribute("aria-invalid", inquiryInput.value ? "false" : "true");
      if (!firstNameInput.value.trim()) {
        setStatus(form, "Please enter your first name.", true);
        firstNameInput.focus();
        return;
      }

      const email = emailInput.value.trim();
      if (!emailPattern.test(email)) {
        emailInput.setAttribute("aria-invalid", "true");
        setStatus(form, "Please enter a valid email address.", true);
        emailInput.focus();
        return;
      }

      if (!inquiryInput.value) {
        setStatus(form, "Please choose what you are contacting Lisa about.", true);
        inquiryInput.focus();
        return;
      }

      emailInput.setAttribute("aria-invalid", "false");
      button.disabled = true;
      button.textContent = "Sending...";
      setStatus(form, "Sending...");

      const payload = buildPayload(form, emailInput);
      try {
        await submitToSheet(form, payload);
        form.reset();
        setStatus(form, "Thank you. I'll be in touch at the email address you provided.");
      } catch (error) {
        console.warn("Discovery call form submission failed:", error);
        setStatus(form, "I'm sorry, your request did not go through. Please try again.", true);
      } finally {
        button.disabled = false;
        button.textContent = initialButtonText;
      }
    });
  });
})();

(() => {
  const forms = Array.from(document.querySelectorAll("[data-newsletter-form]"));
  if (!forms.length) return;

  const liveHost = "www.enlightenedpathhealing.com";
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function endpointRoot(form) {
    const host = window.location.hostname;
    const isLiveDomain = host === liveHost || host.endsWith(".enlightenedpathhealing.com");
    return isLiveDomain ? "" : (form.dataset.endpointRoot || `https://${liveHost}`);
  }

  function setStatus(form, message, isError = false) {
    const status = form.querySelector("[data-newsletter-status]");
    if (!status) return;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
  }

  function buildPayload(form, key) {
    const emailField = form.querySelector(".form-item.email");
    const emailInput = form.querySelector('input[type="email"]');
    const formValues = {
      [emailField?.id || "email"]: emailInput?.value.trim() || ""
    };
    const payload = new URLSearchParams();
    payload.set("formId", form.dataset.formId || "");
    payload.set("collectionId", form.dataset.collectionId || "");
    payload.set("objectName", form.dataset.objectName || "");
    payload.set("key", key);
    payload.set("form", JSON.stringify(formValues));
    payload.set("pageTitle", form.dataset.pageTitle || document.title);
    payload.set("pagePath", form.dataset.pagePath || window.location.pathname);
    payload.set("pageId", form.dataset.collectionId || "");
    payload.set("contentSource", "c");
    payload.set("pagePermissionTypeValue", "1");
    return payload;
  }

  async function submitToSquarespace(form) {
    const root = endpointRoot(form);
    const requestOptions = {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
      }
    };
    const keyResponse = await fetch(`${root}/api/form/FormSubmissionKey`, requestOptions);
    if (!keyResponse.ok) throw new Error("Unable to get form key");
    const keyData = await keyResponse.json();
    const key = keyData && keyData.key;
    if (!key) throw new Error("Missing form key");

    const saveResponse = await fetch(`${root}/api/form/SaveFormSubmission`, {
      ...requestOptions,
      body: buildPayload(form, key)
    });
    if (!saveResponse.ok) throw new Error("Unable to save form submission");
    return saveResponse;
  }

  forms.forEach((form) => {
    const button = form.querySelector('button[type="submit"]');
    const emailInput = form.querySelector('input[type="email"]');
    const initialButtonText = button ? button.textContent.trim() : "Sign Up";

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!emailInput || !button) return;

      const email = emailInput.value.trim();
      if (!emailPattern.test(email)) {
        emailInput.setAttribute("aria-invalid", "true");
        setStatus(form, "Please enter a valid email address.", true);
        emailInput.focus();
        return;
      }

      emailInput.setAttribute("aria-invalid", "false");
      button.disabled = true;
      button.textContent = "Signing Up...";
      setStatus(form, "Submitting...");

      try {
        await submitToSquarespace(form);
        emailInput.value = "";
        setStatus(form, "Thank you. You are on the list.");
      } catch (error) {
        console.warn("Newsletter signup fallback used:", error);
        setStatus(form, "The live signup is available through the link below.", true);
      } finally {
        button.disabled = false;
        button.textContent = initialButtonText;
      }
    });
  });
})();
