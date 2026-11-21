(function () {
  "use strict";

  function getCsrfToken() {
    const tokenInput = document.querySelector(
      'input[name="csrfmiddlewaretoken"]',
    );
    return tokenInput ? tokenInput.value : "";
  }

  async function request(url, options) {
    const response = await fetch(url, options);
    let data;
    try {
      data = await response.json();
    } catch (error) {
      throw new Error("El servidor devolvió una respuesta que no es JSON.");
    }

    if (!response.ok) {
      const requestError = new Error(
        data.error || `La solicitud falló (${response.status}).`,
      );
      requestError.status = response.status;
      requestError.data = data;
      throw requestError;
    }
    return data;
  }

  window.SimulatorApi = {
    get(url) {
      return request(url, {
        headers: { Accept: "application/json" },
      });
    },
    post(url, payload) {
      return request(url, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(payload),
      });
    },
  };
})();
