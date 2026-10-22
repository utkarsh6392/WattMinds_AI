
"use strict";

/*
====================================================
 WATTMINDS - SUPABASE AUTHENTICATION
====================================================

 Features:
 - Email and password login
 - New user registration
 - Email confirmation
 - Forgot password
 - Reset password
 - Persistent sessions
 - User profile
 - Secure logout
 - Supabase token access for FastAPI

 IMPORTANT:
 Supabase URL and public key are loaded
 from the FastAPI /api/public-config endpoint.

 Do not place secret/service_role keys here.
====================================================
*/

(function () {

  // ----------------------------------
  // 1. GLOBAL AUTH STATE
  // ----------------------------------

  const $ = (id) => document.getElementById(id);

  let client = null;
  let mode = "login";
  let recovering = false;

  let resolveReady;

  const ready = new Promise((resolve) => {
    resolveReady = resolve;
  });

  // Expose authentication methods to app.js.
  window.WattAuth = {

    ready,

    async getAccessToken() {

      if (!client) {
        return null;
      }

      const { data, error } =
        await client.auth.getSession();

      if (error) {
        return null;
      }

      return data.session?.access_token || null;
    }

  };


  // ----------------------------------
  // 2. SHOW AUTH MESSAGES
  // ----------------------------------

  function notice(message, type = "") {

    const element = $("auth-message");

    if (!element) {
      return;
    }

    element.textContent = message;

    element.className =
      "auth-message " + type;
  }


  // ----------------------------------
  // 3. LOGIN / SIGNUP MODE
  // ----------------------------------

  function setMode(nextMode) {

    mode = nextMode;

    const signup = nextMode === "signup";

    $("auth-name-wrap").classList.toggle(
      "hidden",
      !signup
    );

    $("auth-confirm-wrap").classList.toggle(
      "hidden",
      !signup
    );

    $("auth-forgot-wrap").classList.toggle(
      "hidden",
      signup
    );

    $("auth-confirm").required = signup;
    $("auth-name").required = signup;

    $("auth-password").autocomplete =
      signup
        ? "new-password"
        : "current-password";

    $("auth-title").textContent =
      signup
        ? "Create your account"
        : "Welcome back";

    $("auth-subtitle").textContent =
      signup
        ? "Start your WattMinds energy journey."
        : "Sign in to your energy workspace.";

    $("auth-submit").textContent =
      signup
        ? "Create account →"
        : "Sign in →";

    for (const tab of ["login", "signup"]) {

      const selected = tab === nextMode;

      const button = $("auth-tab-" + tab);

      button.classList.toggle(
        "selected",
        selected
      );

      button.setAttribute(
        "aria-selected",
        String(selected)
      );
    }

    notice("");
  }


  // ----------------------------------
  // 4. UPDATE USER INTERFACE
  // ----------------------------------

  function setUser(user) {

    const isLoggedIn =
      Boolean(user) && !recovering;

    document.body.classList.toggle(
      "authenticated",
      isLoggedIn
    );

    document.body.classList.remove(
      "auth-loading"
    );

    if (!user) {

      $("user-dropdown").classList.add(
        "hidden"
      );

      return;
    }

    const name =
      user.user_metadata?.full_name ||
      user.email?.split("@")[0] ||
      "Member";

    $("user-display-name").textContent =
      name;

    $("user-email").textContent =
      user.email || "";

    $("user-avatar").textContent =
      name.charAt(0).toUpperCase();
  }


  // ----------------------------------
  // 5. RESTORE USER SESSION
  // ----------------------------------

  async function restoreSession() {

    /*
      getUser verifies the current user
      with Supabase Auth rather than
      trusting only a locally stored object.
    */

    const { data, error } =
      await client.auth.getUser();

    if (error) {

      setUser(null);

      return;
    }

    setUser(data.user);
  }


  // ----------------------------------
  // 6. LOGIN / SIGNUP HANDLER
  // ----------------------------------

  async function submitAuth(event) {

    event.preventDefault();

    const button = $("auth-submit");

    const email =
      $("auth-email").value.trim();

    const password =
      $("auth-password").value;

    const name =
      $("auth-name").value.trim();

    const signup = mode === "signup";

    if (!client) {

      notice(
        "Supabase is not configured.",
        "error"
      );

      return;
    }

    // Validate full name during signup.
    if (signup && name.length < 2) {

      notice(
        "Enter your full name.",
        "error"
      );

      return;
    }

    // Check both passwords match.
    if (
      signup &&
      password !== $("auth-confirm").value
    ) {

      notice(
        "Passwords do not match.",
        "error"
      );

      return;
    }

    button.disabled = true;

    button.textContent =
      "Please wait...";

    notice("");

    try {

      // -------------------------------
      // CREATE ACCOUNT
      // -------------------------------

      if (signup) {

        const { data, error } =
          await client.auth.signUp({

            email,

            password,

            options: {

              data: {
                full_name: name
              },

              emailRedirectTo:
                location.origin + "/"

            }

          });

        if (error) {
          throw error;
        }

        /*
          If email confirmation is enabled,
          Supabase may not create an active
          session immediately.
        */

        if (!data.session) {

          notice(
            "Check your inbox and confirm your email, then log in.",
            "success"
          );

          return;
        }

        setUser(data.user);

      } else {

        // -------------------------------
        // LOGIN EXISTING USER
        // -------------------------------

        const { data, error } =
          await client.auth.signInWithPassword({

            email,

            password

          });

        if (error) {
          throw error;
        }

        setUser(data.user);
      }

    } catch (error) {

      notice(
        error.message ||
        "Authentication failed.",
        "error"
      );

    } finally {

      button.disabled = false;

      button.textContent =
        signup
          ? "Create account →"
          : "Sign in →";
    }
  }


  // ----------------------------------
  // 7. RESET PASSWORD
  // ----------------------------------

  async function resetPassword(event) {

    event.preventDefault();

    const password =
      $("reset-password").value;

    const confirmPassword =
      $("reset-confirm").value;

    if (password !== confirmPassword) {

      $("reset-message").textContent =
        "Passwords do not match.";

      return;
    }

    const button = $("reset-submit");

    button.disabled = true;

    try {

      const { error } =
        await client.auth.updateUser({

          password

        });

      if (error) {
        throw error;
      }

      $("reset-message").textContent =
        "Password updated successfully.";

      recovering = false;

      $("reset-screen").classList.add(
        "hidden"
      );

      const { data } =
        await client.auth.getUser();

      setUser(data.user || null);

      history.replaceState(
        {},
        "",
        "/"
      );

    } catch (error) {

      $("reset-message").textContent =
        error.message;

    } finally {

      button.disabled = false;
    }
  }


  // ----------------------------------
  // 8. INITIALIZE AUTH SYSTEM
  // ----------------------------------

  async function initialize() {

    // Login and signup form.
    $("auth-form").addEventListener(
      "submit",
      submitAuth
    );

    // Password reset form.
    $("reset-form").addEventListener(
      "submit",
      resetPassword
    );

    // Switch to login.
    $("auth-tab-login").addEventListener(
      "click",
      () => setMode("login")
    );

    // Switch to signup.
    $("auth-tab-signup").addEventListener(
      "click",
      () => setMode("signup")
    );


    // ----------------------------------
    // 9. SHOW / HIDE PASSWORD
    // ----------------------------------

    $("auth-toggle-password").addEventListener(
      "click",
      () => {

        const input = $("auth-password");

        input.type =
          input.type === "password"
            ? "text"
            : "password";

        $("auth-toggle-password").textContent =
          input.type === "password"
            ? "Show"
            : "Hide";
      }
    );


    // ----------------------------------
    // 10. FORGOT PASSWORD EMAIL
    // ----------------------------------

    $("auth-forgot").addEventListener(
      "click",
      async () => {

        const email =
          $("auth-email").value.trim();

        if (!email) {

          notice(
            "Enter your email first.",
            "error"
          );

          return;
        }

        if (!client) {

          notice(
            "Supabase is not configured.",
            "error"
          );

          return;
        }

        try {

          const { error } =
            await client.auth.resetPasswordForEmail(
              email,
              {
                redirectTo:
                  location.origin + "/"
              }
            );

          if (error) {
            throw error;
          }

          notice(
            "If the account exists, a recovery email will arrive shortly.",
            "success"
          );

        } catch (error) {

          notice(
            error.message,
            "error"
          );
        }
      }
    );


    // ----------------------------------
    // 11. USER PROFILE DROPDOWN
    // ----------------------------------

    $("user-menu-button").addEventListener(
      "click",
      () => {

        const menu =
          $("user-dropdown");

        menu.classList.toggle(
          "hidden"
        );

        $("user-menu-button").setAttribute(
          "aria-expanded",
          String(
            !menu.classList.contains("hidden")
          )
        );
      }
    );

    // Close menu when clicking outside.
    document.addEventListener(
      "click",
      (event) => {

        if (
          !event.target.closest(
            ".user-menu-wrap"
          )
        ) {

          $("user-dropdown").classList.add(
            "hidden"
          );

          $("user-menu-button").setAttribute(
            "aria-expanded",
            "false"
          );
        }
      }
    );


    // ----------------------------------
    // 12. LOGOUT
    // ----------------------------------

    $("logout-button").addEventListener(
      "click",
      async () => {

        if (!client) {
          return;
        }

        try {

          const { error } =
            await client.auth.signOut();

          if (error) {
            throw error;
          }

          setUser(null);

        } catch (error) {

          alert(
            "Logout failed: " + error.message
          );
        }
      }
    );


    // ----------------------------------
    // 13. LOAD SUPABASE CONFIGURATION
    // ----------------------------------

    try {

      /*
        FastAPI will return:
        {
          "supabase_url": "...",
          "supabase_publishable_key": "..."
        }

        Only public configuration is returned.
      */

      const response =
        await fetch("/api/public-config");

      if (!response.ok) {

        throw new Error(
          "Cannot load Supabase configuration."
        );
      }

      const config =
        await response.json();

      if (
        !config.supabase_url ||
        !config.supabase_publishable_key
      ) {

        throw new Error(
          "Add SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in the server .env file."
        );
      }

      // Check that Supabase JS loaded.
      if (!window.supabase?.createClient) {

        throw new Error(
          "Supabase library not loaded. Check internet/CDN connectivity."
        );
      }


      // ----------------------------------
      // 14. CREATE SUPABASE CLIENT
      // ----------------------------------

      client = window.supabase.createClient(

        config.supabase_url,

        config.supabase_publishable_key,

        {
          auth: {

            persistSession: true,

            autoRefreshToken: true,

            detectSessionInUrl: true

          }
        }
      );


      // ----------------------------------
      // 15. AUTH STATE LISTENER
      // ----------------------------------

      client.auth.onAuthStateChange(
        (event, session) => {

          // Password recovery link opened.
          if (event === "PASSWORD_RECOVERY") {

            recovering = true;

            document.body.classList.remove(
              "authenticated"
            );

            document.body.classList.remove(
              "auth-loading"
            );

            $("reset-screen").classList.remove(
              "hidden"
            );

          } else if (event === "SIGNED_OUT") {

            recovering = false;

            $("reset-screen").classList.add(
              "hidden"
            );

            setUser(null);

          } else if (
            event === "SIGNED_IN" ||
            event === "USER_UPDATED" ||
            event === "TOKEN_REFRESHED"
          ) {

            if (!recovering) {

              setUser(
                session?.user || null
              );
            }
          }
        }
      );


      // Restore user after page refresh.
      await restoreSession();

    } catch (error) {

      document.body.classList.remove(
        "auth-loading"
      );

      notice(
        error.message ||
        "Authentication is unavailable.",
        "error"
      );

    } finally {

      /*
        app.js waits for WattAuth.ready
        before making authenticated requests.
      */

      resolveReady();
    }
  }

  initialize();

})();
