/* manuscripts.js — CatholicJarvis Manuscript Paleography Suite
   Path: static/modules/manuscripts.js
   Part of CatholicJarvis Master Work Suite. Uses jarvis.css tokens only (no hardcoded hex).
*/
(function () {
  "use strict";

  window.JarvisModules = window.JarvisModules || {};

  var state = {
    manuscripts: [],
    selectedMs: "codex_vaticanus",
    selectedFolio: "p1303_luke1",
    currentData: null,
    viewMode: "normal", // normal, raking, uv, invert
    rakingAngle: 45,
    rakingElevation: 25,
    rakingIntensity: 85,
    uvIntensity: 80,
    pageCurl: 65, // 0 to 100 percent cockling/gutter curl
    selectedWordIndex: null,
    filterQuery: "",
    // 3D Engine objects
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    parchmentMesh: null,
    parchmentGeom: null,
    parchmentMat: null,
    diffuseTexture: null,
    normalTexture: null,
    rakingLight: null,
    rakingGizmo: null,
    ambientLight: null,
    dirLight: null,
    animId: null,
    containerElem: null
  };

  function el(tag, attrs, children) {
    var elem = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "text") elem.textContent = attrs[k];
        else if (k === "html") elem.innerHTML = attrs[k];
        else if (k === "style") elem.style.cssText = attrs[k];
        else if (k === "on") {
          Object.keys(attrs.on).forEach(function (ev) {
            elem.addEventListener(ev, attrs.on[ev]);
          });
        } else elem.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      if (c) elem.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return elem;
  }

  function fetchManuscripts(cb) {
    fetch("/api/manuscripts")
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (data) {
        state.manuscripts = data || [];
        if (cb) cb();
      })
      .catch(function (err) {
        console.error("Failed to load manuscripts:", err);
      });
  }

  function fetchFolio(msId, folioId, cb) {
    fetch("/api/manuscripts/" + encodeURIComponent(msId) + "/folio/" + encodeURIComponent(folioId))
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        state.currentData = data;
        if (cb) cb();
      })
      .catch(function (err) {
        console.error("Failed to load folio:", err);
      });
  }

  function copyTextToClipboard(text, btn) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        var old = btn.textContent;
        btn.textContent = "✓ Copied!";
        setTimeout(function () { btn.textContent = old; }, 1800);
      });
    } else {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      var old = btn.textContent;
      btn.textContent = "✓ Copied!";
      setTimeout(function () { btn.textContent = old; }, 1800);
    }
  }

  // ── 3D Procedural Texture Generator ────────────────────────────────────────
  function createParchmentCanvasTexture(folio, mode) {
    var c = document.createElement("canvas");
    c.width = 1200;
    c.height = 1600;
    var ctx = c.getContext("2d");

    var isHebrew = state.selectedMs === "great_isaiah_scroll" || state.selectedMs === "scroll_4qmmt";
    var isPapyrus = state.selectedMs.indexOf("papyrus") !== -1;

    // 1. Base Substrate Gradient
    var grad = ctx.createLinearGradient(0, 0, c.width, c.height);
    if (mode === "invert") {
      grad.addColorStop(0, "rgb(18, 21, 31)");
      grad.addColorStop(1, "rgb(28, 33, 48)");
    } else if (mode === "uv") {
      // 365nm Wood's lamp excitation
      grad.addColorStop(0, "rgb(24, 18, 48)");
      grad.addColorStop(0.5, "rgb(32, 22, 64)");
      grad.addColorStop(1, "rgb(20, 14, 40)");
    } else if (isPapyrus) {
      // Aged fibrous Egyptian papyrus reed texture
      grad.addColorStop(0, "rgb(218, 196, 154)");
      grad.addColorStop(0.5, "rgb(204, 180, 136)");
      grad.addColorStop(1, "rgb(186, 160, 116)");
    } else if (isHebrew) {
      // Ancient Judean Desert tanned leather scroll tone
      grad.addColorStop(0, "rgb(212, 188, 146)");
      grad.addColorStop(0.5, "rgb(198, 172, 130)");
      grad.addColorStop(1, "rgb(175, 148, 108)");
    } else {
      // Premium Constantinian calfskin / sheepskin vellum
      grad.addColorStop(0, "rgb(244, 234, 210)");
      grad.addColorStop(0.5, "rgb(234, 220, 190)");
      grad.addColorStop(1, "rgb(214, 198, 162)");
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, c.width, c.height);

    // 2. Natural Micro-Texture & Cockling Stipple
    var noiseCount = isPapyrus ? 3500 : 1800;
    for (var n = 0; n < noiseCount; n++) {
      var nx = Math.random() * c.width;
      var ny = Math.random() * c.height;
      var nw = isPapyrus ? Math.random() * 30 + 4 : Math.random() * 4 + 1;
      var nh = isPapyrus ? (Math.random() < 0.5 ? 2 : 18) : Math.random() * 4 + 1;
      var alpha = mode === "uv" ? 0.04 : 0.06;
      ctx.fillStyle = mode === "uv" ? "rgba(167, 139, 250, " + alpha + ")" : "rgba(110, 85, 45, " + alpha + ")";
      ctx.fillRect(nx, ny, nw, nh);
    }

    // 3. Aged Page Perimeter Burnishing & Gutter Shadows
    var borderGrad = ctx.createRadialGradient(c.width / 2, c.height / 2, c.width * 0.38, c.width / 2, c.height / 2, c.width * 0.72);
    if (mode === "uv") {
      borderGrad.addColorStop(0, "rgba(0, 0, 0, 0)");
      borderGrad.addColorStop(1, "rgba(15, 10, 30, 0.7)");
    } else {
      borderGrad.addColorStop(0, "rgba(0, 0, 0, 0)");
      borderGrad.addColorStop(0.7, "rgba(140, 110, 70, 0.15)");
      borderGrad.addColorStop(1, "rgba(90, 65, 35, 0.5)");
    }
    ctx.fillStyle = borderGrad;
    ctx.fillRect(0, 0, c.width, c.height);

    // 4. Pricking Holes & Dry-Point Ruling Lines
    ctx.strokeStyle = mode === "uv" ? "rgba(167, 139, 250, 0.16)" : "rgba(170, 145, 105, 0.32)";
    ctx.lineWidth = 1;
    var lineStep = isHebrew ? 46 : 42;
    var startRuling = 140;
    for (var ry = startRuling; ry < c.height - 120; ry += lineStep) {
      ctx.beginPath();
      ctx.moveTo(80, ry);
      ctx.lineTo(c.width - 80, ry);
      ctx.stroke();

      // Pricking dots along margin
      ctx.fillStyle = mode === "uv" ? "rgba(167, 139, 250, 0.25)" : "rgba(120, 95, 60, 0.35)";
      ctx.fillRect(68, ry - 1, 3, 3);
      ctx.fillRect(c.width - 72, ry - 1, 3, 3);
    }

    // 5. Uncial Text Rendering
    ctx.textAlign = isHebrew ? "right" : "left";
    ctx.textBaseline = "alphabetic";

    if (folio && folio.lines && folio.lines.length > 0) {
      var lines = folio.lines;
      var textStartY = 176;

      lines.forEach(function (ln, i) {
        var y = textStartY + i * lineStep;
        if (y > c.height - 100) return;

        if (mode === "uv") {
          // Fluorescent neon green/cyan emission under 365nm UV
          ctx.fillStyle = "rgba(110, 231, 183, 0.95)";
          ctx.shadowColor = "rgba(52, 211, 153, 0.85)";
          ctx.shadowBlur = 10;
        } else if (mode === "invert") {
          ctx.fillStyle = "rgba(241, 245, 249, 0.95)";
          ctx.shadowBlur = 0;
        } else {
          // Authentic ancient carbon or iron-gall ink with slight organic erosion
          ctx.fillStyle = "rgba(42, 32, 22, 0.94)";
          ctx.shadowBlur = 0;
        }

        if (isHebrew) {
          ctx.font = "bold 26px 'Times New Roman', serif";
          ctx.fillText(ln.uncial, c.width - 110, y);
        } else {
          ctx.font = "bold 23px 'Cinzel', serif";
          ctx.fillText(ln.uncial, 110, y);
        }
      });
      ctx.shadowBlur = 0;
    }

    return new THREE.CanvasTexture(c);
  }

  // ── Procedural Normal Map for Parchment Fiber Topography ──────────────────
  function createParchmentNormalTexture() {
    var c = document.createElement("canvas");
    c.width = 512;
    c.height = 512;
    var ctx = c.getContext("2d");
    var imgData = ctx.createImageData(c.width, c.height);
    var data = imgData.data;

    for (var y = 0; y < c.height; y++) {
      for (var x = 0; x < c.width; x++) {
        var idx = (y * c.width + x) * 4;
        // Fine normal bump perturbation (tangent space: 128, 128, 255 is flat surface)
        var waveX = Math.sin(x * 0.15) * Math.cos(y * 0.08) * 16;
        var waveY = Math.cos(x * 0.12) * Math.sin(y * 0.18) * 16;
        var noise = (Math.random() - 0.5) * 18;

        data[idx] = Math.max(0, Math.min(255, 128 + waveX + noise));     // Red (X normal)
        data[idx + 1] = Math.max(0, Math.min(255, 128 + waveY + noise)); // Green (Y normal)
        data[idx + 2] = 240;                                             // Blue (Z normal)
        data[idx + 3] = 255;
      }
    }
    ctx.putImageData(imgData, 0, 0);
    var tex = new THREE.CanvasTexture(c);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.repeat.set(4, 5);
    return tex;
  }

  // ── Vertex Displacement: Natural Page Cockling & Gutter Curl ──────────────
  function applyParchmentCurvature(intensityPct) {
    if (!state.parchmentGeom) return;

    var pos = state.parchmentGeom.attributes.position;
    var intensity = (intensityPct / 100);

    for (var i = 0; i < pos.count; i++) {
      var x = pos.getX(i);
      var y = pos.getY(i);

      // Gutter curve near left binding (x < -1.0)
      var gutterDist = (x + 1.8) / 3.6; // 0 at left edge, 1 at right edge
      var gutterCurl = Math.pow(Math.max(0, 0.45 - gutterDist), 2) * 1.2;

      // Natural parchment cockling (wave displacement across sheepskin fibers)
      var cockleWave = Math.sin(x * 2.4) * Math.cos(y * 1.8) * 0.08 +
                       Math.sin(x * 5.2 + y * 4.1) * 0.025 +
                       Math.cos(y * 3.6) * 0.04;

      // Subtle outer edge droop
      var edgeDroop = Math.pow(Math.max(0, gutterDist - 0.75) / 0.25, 2) * 0.15;

      var z = (gutterCurl + cockleWave - edgeDroop) * intensity;
      pos.setZ(i, z);
    }

    pos.needsUpdate = true;
    state.parchmentGeom.computeVertexNormals();
  }

  // ── 3D Scene Initialization ───────────────────────────────────────────────
  function initThreeScene(canvasContainer) {
    if (state.renderer) {
      if (state.animId) cancelAnimationFrame(state.animId);
      if (state.renderer.domElement && state.renderer.domElement.parentNode) {
        state.renderer.domElement.parentNode.removeChild(state.renderer.domElement);
      }
      state.renderer.dispose();
      state.renderer = null;
    }

    var w = canvasContainer.clientWidth || 700;
    var h = canvasContainer.clientHeight || 750;

    // 1. Scene & Camera
    state.scene = new THREE.Scene();
    state.camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 100);
    state.camera.position.set(0, 0, 5.4);

    // 2. WebGL Renderer with High-Precision Shadow Maps
    state.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    state.renderer.setSize(w, h);
    state.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    state.renderer.shadowMap.enabled = true;
    state.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    state.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    state.renderer.toneMappingExposure = 1.05;
    canvasContainer.appendChild(state.renderer.domElement);

    // 3. OrbitControls
    state.controls = new THREE.OrbitControls(state.camera, state.renderer.domElement);
    state.controls.enableDamping = true;
    state.controls.dampingFactor = 0.06;
    state.controls.maxPolarAngle = Math.PI / 2 + 0.15;
    state.controls.minDistance = 1.2;
    state.controls.maxDistance = 12.0;

    // 4. Lighting System
    state.ambientLight = new THREE.AmbientLight(0xfff8ed, 0.65);
    state.scene.add(state.ambientLight);

    state.dirLight = new THREE.DirectionalLight(0xffffff, 0.5);
    state.dirLight.position.set(2, 4, 5);
    state.scene.add(state.dirLight);

    // Raking Point Light & Visible Lamp Gizmo
    state.rakingLight = new THREE.PointLight(0xfff5d6, 1.8, 15, 1.2);
    state.rakingLight.castShadow = true;
    state.rakingLight.shadow.mapSize.width = 1024;
    state.rakingLight.shadow.mapSize.height = 1024;
    state.scene.add(state.rakingLight);

    var bulbGeom = new THREE.SphereGeometry(0.07, 16, 16);
    var bulbMat = new THREE.MeshBasicMaterial({ color: 0xffe066 });
    state.rakingGizmo = new THREE.Mesh(bulbGeom, bulbMat);
    state.scene.add(state.rakingGizmo);

    updateRakingLightTransform();

    // 5. Procedural 3D Parchment Mesh (3.6 x 4.8 units, 64x64 vertices)
    state.parchmentGeom = new THREE.PlaneGeometry(3.6, 4.8, 64, 64);
    applyParchmentCurvature(state.pageCurl);

    state.normalTexture = createParchmentNormalTexture();
    var folio = state.currentData ? state.currentData.folio : null;
    state.diffuseTexture = createParchmentCanvasTexture(folio, state.viewMode);

    state.parchmentMat = new THREE.MeshStandardMaterial({
      map: state.diffuseTexture,
      normalMap: state.normalTexture,
      normalScale: new THREE.Vector2(0.65, 0.65),
      roughness: 0.86,
      metalness: 0.02,
      side: THREE.DoubleSide
    });

    state.parchmentMesh = new THREE.Mesh(state.parchmentGeom, state.parchmentMat);
    state.parchmentMesh.receiveShadow = true;
    state.parchmentMesh.castShadow = true;
    state.scene.add(state.parchmentMesh);

    // Apply Lighting & Shaders based on mode
    applyViewModeParameters();

    // 6. Render Loop
    function animate() {
      state.animId = requestAnimationFrame(animate);
      if (state.controls) state.controls.update();
      if (state.renderer && state.scene && state.camera) {
        state.renderer.render(state.scene, state.camera);
      }
    }
    animate();

    // Resize Observer
    var ro = new ResizeObserver(function () {
      if (!canvasContainer || !state.renderer || !state.camera) return;
      var nw = canvasContainer.clientWidth;
      var nh = canvasContainer.clientHeight;
      if (nw === 0 || nh === 0) return;
      state.camera.aspect = nw / nh;
      state.camera.updateProjectionMatrix();
      state.renderer.setSize(nw, nh);
    });
    ro.observe(canvasContainer);
  }

  function updateRakingLightTransform() {
    if (!state.rakingLight || !state.rakingGizmo) return;

    var radAzimuth = (state.rakingAngle * Math.PI) / 180;
    var radElev = (state.rakingElevation * Math.PI) / 180;
    var radius = 3.6;

    var lx = Math.cos(radAzimuth) * Math.cos(radElev) * radius;
    var ly = Math.sin(radAzimuth) * Math.cos(radElev) * radius;
    var lz = Math.sin(radElev) * radius + 0.3;

    state.rakingLight.position.set(lx, ly, lz);
    state.rakingGizmo.position.set(lx, ly, lz);

    var intensityNorm = (state.rakingIntensity / 100);
    state.rakingLight.intensity = intensityNorm * 2.6;
  }

  function applyViewModeParameters() {
    if (!state.parchmentMat || !state.ambientLight || !state.dirLight || !state.rakingLight) return;

    var folio = state.currentData ? state.currentData.folio : null;

    if (state.diffuseTexture) state.diffuseTexture.dispose();
    state.diffuseTexture = createParchmentCanvasTexture(folio, state.viewMode);
    state.parchmentMat.map = state.diffuseTexture;

    if (state.viewMode === "raking") {
      // Raking light: low ambient, directional accent, high grazing relief shadows
      state.ambientLight.color.setHex(0x221a14);
      state.ambientLight.intensity = 0.35;
      state.dirLight.intensity = 0.15;
      state.rakingLight.visible = true;
      state.rakingGizmo.visible = true;
      state.parchmentMat.emissive.setHex(0x000000);
      state.parchmentMat.roughness = 0.92;
      state.parchmentMat.normalScale.set(1.4, 1.4);
    } else if (state.viewMode === "uv") {
      // 365nm UV multi-spectral mode: deep dark indigo ambient with glowing ink emission
      state.ambientLight.color.setHex(0x201442);
      state.ambientLight.intensity = 0.45;
      state.dirLight.intensity = 0.1;
      state.rakingLight.visible = false;
      state.rakingGizmo.visible = false;
      var uvNorm = state.uvIntensity / 100;
      state.parchmentMat.emissive.setHex(0x0a2618);
      state.parchmentMat.emissiveIntensity = uvNorm * 0.9;
      state.parchmentMat.roughness = 0.75;
      state.parchmentMat.normalScale.set(0.4, 0.4);
    } else if (state.viewMode === "invert") {
      state.ambientLight.color.setHex(0xd0d4dc);
      state.ambientLight.intensity = 0.7;
      state.dirLight.intensity = 0.6;
      state.rakingLight.visible = false;
      state.rakingGizmo.visible = false;
      state.parchmentMat.emissive.setHex(0x000000);
      state.parchmentMat.normalScale.set(0.5, 0.5);
    } else {
      // True Color Archival Normal
      state.ambientLight.color.setHex(0xfffaea);
      state.ambientLight.intensity = 0.75;
      state.dirLight.intensity = 0.55;
      state.rakingLight.visible = false;
      state.rakingGizmo.visible = false;
      state.parchmentMat.emissive.setHex(0x000000);
      state.parchmentMat.roughness = 0.86;
      state.parchmentMat.normalScale.set(0.65, 0.65);
    }

    state.parchmentMat.needsUpdate = true;
  }

  // ── Camera Preset Positions ───────────────────────────────────────────────
  function setCameraPreset(preset) {
    if (!state.camera || !state.controls) return;

    if (preset === "face_on") {
      state.camera.position.set(0, 0, 5.4);
      state.controls.target.set(0, 0, 0);
    } else if (preset === "raking_angle") {
      state.camera.position.set(1.9, -2.4, 2.2);
      state.controls.target.set(0, 0, 0);
    } else if (preset === "macro") {
      state.camera.position.set(0.3, 0.9, 1.35);
      state.controls.target.set(0.1, 0.8, 0);
    } else if (preset === "gutter") {
      state.camera.position.set(-2.6, -1.1, 2.9);
      state.controls.target.set(-0.8, 0, 0);
    }
    state.controls.update();
  }

  // ── Main UI Rendering ─────────────────────────────────────────────────────
  function render(container) {
    state.containerElem = container;
    container.textContent = "";
    container.style.cssText = "display: flex; flex-direction: column; height: 100%; overflow: hidden; background: var(--bg-base); color: var(--text-main); font-family: var(--font-ui);";

    // ── 1. Top Header Toolbar ────────────────────────────────────────────────
    var topBar = el("div", {
      style: "display: flex; align-items: center; justify-content: space-between; padding: var(--sp-2) var(--sp-4); background: var(--bg-panel); border-bottom: 1px solid var(--border); flex-shrink: 0; gap: var(--sp-3); flex-wrap: wrap;"
    });

    var leftControls = el("div", { style: "display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap;" });

    // Manuscript Title & Siglum Select
    var msSelect = el("select", {
      style: "background: var(--bg-card); color: var(--text-main); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-1) var(--sp-3); font-weight: 600; font-size: var(--fs-xs); cursor: pointer; max-width: 270px;",
      on: {
        change: function (e) {
          state.selectedMs = e.target.value;
          state.selectedWordIndex = null;
          fetch("/api/manuscripts/" + encodeURIComponent(state.selectedMs))
            .then(function (r) { return r.json(); })
            .then(function (ms) {
              if (ms && ms.folios && ms.folios.length > 0) {
                state.selectedFolio = ms.folios[0].id;
              }
              fetchFolio(state.selectedMs, state.selectedFolio, function () {
                render(container);
              });
            });
        }
      }
    });

    state.manuscripts.forEach(function (m) {
      var opt = el("option", { value: m.id, text: m.name + " (" + m.siglum + ")" });
      if (m.id === state.selectedMs) opt.selected = true;
      msSelect.appendChild(opt);
    });
    leftControls.appendChild(msSelect);

    // Folio Selector
    var folSelect = el("select", {
      style: "background: var(--bg-card); color: var(--text-main); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-1) var(--sp-3); font-size: var(--fs-xs); cursor: pointer; max-width: 310px;",
      on: {
        change: function (e) {
          state.selectedFolio = e.target.value;
          state.selectedWordIndex = null;
          fetchFolio(state.selectedMs, state.selectedFolio, function () {
            render(container);
          });
        }
      }
    });

    if (state.currentData && state.currentData.folio) {
      fetch("/api/manuscripts/" + encodeURIComponent(state.selectedMs))
        .then(function (r) { return r.json(); })
        .then(function (m) {
          folSelect.textContent = "";
          (m.folios || []).forEach(function (f) {
            var opt = el("option", { value: f.id, text: f.label + " [" + f.passage + "]" });
            if (f.id === state.selectedFolio) opt.selected = true;
            folSelect.appendChild(opt);
          });
        });
    }
    leftControls.appendChild(folSelect);
    topBar.appendChild(leftControls);

    // Right tools: View Mode Buttons, Camera Presets, Citation button
    var rightControls = el("div", { style: "display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap;" });

    // Mode Buttons: Normal, Raking Light, UV Fluorescence, Invert
    var modes = [
      { id: "normal", label: "True Color", ico: "👁" },
      { id: "raking", label: "Raking Light (3D)", ico: "🔦" },
      { id: "uv", label: "UV Multi-Spectral", ico: "✨" },
      { id: "invert", label: "High Contrast", ico: "🌓" }
    ];

    modes.forEach(function (mode) {
      var isAct = state.viewMode === mode.id;
      var btn = el("button", {
        style: "background: " + (isAct ? "var(--accent-gold)" : "var(--bg-card)") + "; color: " + (isAct ? "var(--on-gold)" : "var(--text-main)") + "; border: 1px solid " + (isAct ? "var(--accent-gold)" : "var(--border)") + "; border-radius: var(--radius); padding: var(--sp-1) var(--sp-2); font-size: var(--fs-xs); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;",
        text: mode.ico + " " + mode.label,
        on: {
          click: function () {
            state.viewMode = mode.id;
            applyViewModeParameters();
            render(container);
          }
        }
      });
      rightControls.appendChild(btn);
    });

    // Camera Presets Group
    var camGroup = el("div", { style: "display: flex; align-items: center; gap: 2px; background: var(--bg-card); padding: 2px; border-radius: var(--radius); border: 1px solid var(--border);" });
    var camPresets = [
      { id: "face_on", label: "📐 Flat" },
      { id: "raking_angle", label: "🔦 Relief" },
      { id: "macro", label: "🔬 Macro" },
      { id: "gutter", label: "📖 Spine" }
    ];
    camPresets.forEach(function (cp) {
      var cBtn = el("button", {
        style: "background: none; border: none; color: var(--text-muted); font-size: var(--fs-xs); padding: 2px 7px; border-radius: 3px; cursor: pointer;",
        text: cp.label,
        on: {
          click: function () {
            setCameraPreset(cp.id);
          }
        }
      });
      camGroup.appendChild(cBtn);
    });
    rightControls.appendChild(camGroup);

    // Cite Button (SBL)
    var citeBtn = el("button", {
      style: "background: var(--accent-blue); color: var(--on-accent); border: none; border-radius: var(--radius); padding: var(--sp-1) var(--sp-3); font-size: var(--fs-xs); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;",
      text: "📜 Copy Citation",
      on: {
        click: function () {
          fetch("/api/manuscripts/cite", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ms_id: state.selectedMs, folio_id: state.selectedFolio, style: "sbl" })
          })
            .then(function (r) { return r.json(); })
            .then(function (res) {
              copyTextToClipboard(res.sbl, citeBtn);
            });
        }
      }
    });
    rightControls.appendChild(citeBtn);

    // Logos / Verbum Copy Button
    var logosBtn = el("button", {
      style: "background: var(--accent-gold); color: var(--on-gold); border: none; border-radius: var(--radius); padding: var(--sp-1) var(--sp-3); font-size: var(--fs-xs); font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;",
      text: "📖 Copy Logos/Verbum",
      on: {
        click: function () {
          fetch("/api/manuscripts/cite", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ms_id: state.selectedMs, folio_id: state.selectedFolio, style: "logos_verbum" })
          })
            .then(function (r) { return r.json(); })
            .then(function (res) {
              copyTextToClipboard(res.logos_verbum, logosBtn);
            });
        }
      }
    });
    rightControls.appendChild(logosBtn);

    topBar.appendChild(rightControls);
    container.appendChild(topBar);

    // ── 2. Main Workspace Split Layout (3D Left, Inspector Right) ───────────
    var mainArea = el("div", {
      style: "display: flex; flex: 1; min-height: 0; overflow: hidden;"
    });

    // ── 2A. Left Pane: 3D Interactive WebGL Parchment Laboratory ────────────
    var canvasPane = el("div", {
      style: "flex: 1.3; min-width: 0; display: flex; flex-direction: column; background: var(--media-bg); border-right: 1px solid var(--border); position: relative; overflow: hidden;"
    });

    // Interactive Slider Controls Sub-Bar
    var sliderBar = el("div", {
      style: "display: flex; align-items: center; gap: var(--sp-3); padding: var(--sp-1) var(--sp-3); background: var(--bg-panel); border-bottom: 1px solid var(--border); font-size: var(--fs-xs); flex-shrink: 0; flex-wrap: wrap;"
    });

    // Always Available: Parchment Curvature / Cockling Slider
    sliderBar.appendChild(el("span", { style: "color: var(--accent-gold); font-weight: 600;", text: "Parchment Cockling:" }));
    var curlSlider = el("input", {
      type: "range", min: "0", max: "100", value: state.pageCurl.toString(),
      style: "cursor: pointer; width: 85px;",
      on: {
        input: function (e) {
          state.pageCurl = parseInt(e.target.value, 10);
          applyParchmentCurvature(state.pageCurl);
        }
      }
    });
    sliderBar.appendChild(curlSlider);

    if (state.viewMode === "raking") {
      sliderBar.appendChild(el("span", { style: "color: var(--accent-gold); font-weight: 600; margin-left: var(--sp-2);", text: "Lamp Azimuth:" }));
      var angleSlider = el("input", {
        type: "range", min: "0", max: "360", value: state.rakingAngle.toString(),
        style: "cursor: pointer; width: 90px;",
        on: {
          input: function (e) {
            state.rakingAngle = parseInt(e.target.value, 10);
            updateRakingLightTransform();
          }
        }
      });
      sliderBar.appendChild(angleSlider);

      sliderBar.appendChild(el("span", { style: "color: var(--accent-gold); font-weight: 600; margin-left: var(--sp-2);", text: "Grazing Elevation:" }));
      var elevSlider = el("input", {
        type: "range", min: "10", max: "85", value: state.rakingElevation.toString(),
        style: "cursor: pointer; width: 80px;",
        on: {
          input: function (e) {
            state.rakingElevation = parseInt(e.target.value, 10);
            updateRakingLightTransform();
          }
        }
      });
      sliderBar.appendChild(elevSlider);

      sliderBar.appendChild(el("span", { style: "color: var(--accent-gold); font-weight: 600; margin-left: var(--sp-2);", text: "Lamp Intensity:" }));
      var intSlider = el("input", {
        type: "range", min: "20", max: "100", value: state.rakingIntensity.toString(),
        style: "cursor: pointer; width: 80px;",
        on: {
          input: function (e) {
            state.rakingIntensity = parseInt(e.target.value, 10);
            updateRakingLightTransform();
          }
        }
      });
      sliderBar.appendChild(intSlider);
    } else if (state.viewMode === "uv") {
      sliderBar.appendChild(el("span", { style: "color: var(--accent-purple); font-weight: 600; margin-left: var(--sp-2);", text: "365nm UV Fluorescence Excitation:" }));
      var uvSlider = el("input", {
        type: "range", min: "10", max: "100", value: state.uvIntensity.toString(),
        style: "cursor: pointer; width: 100px;",
        on: {
          input: function (e) {
            state.uvIntensity = parseInt(e.target.value, 10);
            applyViewModeParameters();
          }
        }
      });
      sliderBar.appendChild(uvSlider);
    }

    canvasPane.appendChild(sliderBar);

    // 3D Canvas Mounting Viewport
    var canvasWrap = el("div", {
      id: "ms-3d-viewport",
      style: "flex: 1; position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; cursor: grab;"
    });

    // IIIF Anchor Indicator overlay at bottom-left of 3D canvas
    var iiifBadge = el("div", {
      style: "position: absolute; bottom: var(--sp-3); left: var(--sp-3); background: rgba(18, 22, 34, 0.88); backdrop-filter: blur(6px); border: 1px solid var(--border); border-radius: var(--radius); padding: 5px 12px; font-size: var(--fs-xs); font-family: var(--font-mono); color: var(--text-muted); pointer-events: auto; display: flex; align-items: center; gap: 8px; z-index: 10;"
    });
    if (state.currentData && state.currentData.iiif_manifest) {
      var manifestLink = el("a", {
        href: state.currentData.iiif_manifest,
        target: "_blank",
        style: "color: var(--accent-cyan); text-decoration: none; font-weight: 600;",
        text: "IIIF Manifest ↗"
      });
      iiifBadge.appendChild(manifestLink);
      iiifBadge.appendChild(el("span", { text: "· " + (state.currentData.folio ? state.currentData.folio.shelfmark : "") }));
    }
    canvasWrap.appendChild(iiifBadge);

    // 3D Navigation Guide Pill overlay at bottom-right
    var navGuide = el("div", {
      style: "position: absolute; bottom: var(--sp-3); right: var(--sp-3); background: rgba(18, 22, 34, 0.82); backdrop-filter: blur(6px); border: 1px solid var(--border); border-radius: var(--radius); padding: 4px 10px; font-size: var(--fs-xs); color: var(--text-dim); pointer-events: none; z-index: 10;",
      text: "🖱️ Drag: Rotate 3D · Right-Click: Pan · Scroll: Zoom"
    });
    canvasWrap.appendChild(navGuide);

    canvasPane.appendChild(canvasWrap);
    mainArea.appendChild(canvasPane);

    // ── 2B. Right Pane: Paleographical, Textual & Exegetical Inspector ───────
    var inspectPane = el("div", {
      style: "flex: 1.1; min-width: 0; background: var(--bg-panel); overflow-y: auto; padding: var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-4);"
    });

    if (state.currentData && state.currentData.folio) {
      var folio = state.currentData.folio;

      // Card 1: Manuscript Metadata & Shelfmark
      var metaCard = el("div", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3);"
      });
      metaCard.appendChild(el("div", {
        style: "display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--sp-2);"
      }, [
        el("div", {}, [
          el("div", { style: "font-family: var(--font-display); font-size: var(--fs-md); font-weight: 700; color: var(--accent-gold);", text: state.currentData.manuscript_name }),
          el("div", { style: "font-size: var(--fs-xs); color: var(--text-muted); font-family: var(--font-mono);", text: folio.shelfmark + " · " + folio.passage })
        ]),
        el("span", {
          style: "font-size: var(--fs-xs); background: var(--accent-gold-soft); color: var(--accent-gold); padding: 2px 6px; border-radius: var(--radius); font-weight: 600;",
          text: state.currentData.siglum
        })
      ]));
      metaCard.appendChild(el("div", {
        style: "font-size: var(--fs-xs); color: var(--text-dim); line-height: 1.5;",
        text: folio.paleographical_notes
      }));
      inspectPane.appendChild(metaCard);

      // Card 2: Refutation of Skeptical Claims (Theological & Historical Impact)
      if (folio.theological_bearing) {
        var refutationCard = el("div", {
          style: "background: rgba(16, 185, 129, 0.08); border: 1px solid var(--accent-green); border-radius: var(--radius); padding: var(--sp-3);"
        });
        refutationCard.appendChild(el("div", {
          style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-green); margin-bottom: 4px; display: flex; align-items: center; gap: 4px;",
          text: "🛡️ APOSTOLIC DEFENSE & HISTORICAL WITNESS"
        }));
        refutationCard.appendChild(el("div", {
          style: "font-size: var(--fs-xs); color: var(--text-main); line-height: 1.5;",
          text: folio.theological_bearing
        }));
        inspectPane.appendChild(refutationCard);
      }

      // Card 3: Line-by-Line Collation & Transcription
      var transCard = el("div", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3);"
      });
      transCard.appendChild(el("div", {
        style: "font-size: var(--fs-sm); font-weight: 700; color: var(--text-main); margin-bottom: var(--sp-2); display: flex; justify-content: space-between; align-items: center;"
      }, [
        el("span", { text: "📖 Paleographical Transcription" }),
        el("span", { style: "font-size: var(--fs-xs); color: var(--text-dim); font-family: var(--font-mono);", text: "Original Script ➔ Accented Text" })
      ]));

      var linesBox = el("div", {
        style: "display: flex; flex-direction: column; gap: 6px; font-size: var(--fs-xs);"
      });

      (folio.lines || []).forEach(function (ln) {
        var row = el("div", {
          style: "display: grid; grid-template-columns: 32px 1fr 1fr; gap: var(--sp-2); padding: 5px 8px; background: rgba(0,0,0,0.22); border-radius: 4px; align-items: center;"
        });
        row.appendChild(el("span", { style: "color: var(--text-dim); font-family: var(--font-mono);", text: "L" + ln.line_num }));
        row.appendChild(el("span", { style: "font-family: var(--font-mono); color: var(--accent-gold); letter-spacing: 0.5px;", text: ln.uncial }));
        row.appendChild(el("span", { style: "font-family: var(--font-read); font-style: italic; color: var(--text-muted);", text: ln.minuscule }));
        linesBox.appendChild(row);
      });
      transCard.appendChild(linesBox);

      // Latin Vulgate (Verbum Catholic Edition)
      if (folio.vulgate) {
        var vulgateBox = el("div", {
          style: "margin-top: var(--sp-2); padding: var(--sp-2) var(--sp-3); background: rgba(212, 175, 55, 0.08); border-left: 3px solid var(--accent-gold); border-radius: 4px;"
        });
        vulgateBox.appendChild(el("div", {
          style: "font-size: var(--fs-xs); font-weight: 700; color: var(--accent-gold); margin-bottom: 3px; display: flex; align-items: center; gap: 4px;",
          text: "📖 LATIN VULGATE (VERBUM CATHOLIC EDITION)"
        }));
        vulgateBox.appendChild(el("div", {
          style: "font-family: var(--font-read); font-style: italic; font-size: var(--fs-xs); color: var(--text-main); line-height: 1.5;",
          text: folio.vulgate
        }));
        transCard.appendChild(vulgateBox);
      }

      inspectPane.appendChild(transCard);

      // Card 4: Word-by-Word Morphological Lexicon Alignment
      if (folio.words_morph && folio.words_morph.length > 0) {
        var morphCard = el("div", {
          style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3);"
        });
        morphCard.appendChild(el("div", {
          style: "font-size: var(--fs-sm); font-weight: 700; color: var(--accent-cyan); margin-bottom: var(--sp-2);",
          text: "🔍 Word-Level Morphological Alignment (MorphGNT / BDAG / BDB)"
        }));

        var pillsBox = el("div", {
          style: "display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--sp-3);"
        });

        folio.words_morph.forEach(function (w, idx) {
          var isSel = state.selectedWordIndex === idx;
          var pill = el("button", {
            style: "background: " + (isSel ? "var(--accent-cyan)" : "var(--bg-panel)") + "; color: " + (isSel ? "var(--on-accent)" : "var(--text-main)") + "; border: 1px solid " + (isSel ? "var(--accent-cyan)" : "var(--border)") + "; border-radius: 14px; padding: 3px 10px; font-size: var(--fs-xs); font-family: var(--font-mono); cursor: pointer; transition: all 0.15s ease;",
            text: w.word,
            on: {
              click: function () {
                state.selectedWordIndex = isSel ? null : idx;
                render(container);
              }
            }
          });
          pillsBox.appendChild(pill);
        });
        morphCard.appendChild(pillsBox);

        // Display active word details
        if (state.selectedWordIndex !== null && folio.words_morph[state.selectedWordIndex]) {
          var selW = folio.words_morph[state.selectedWordIndex];
          var wDetail = el("div", {
            style: "padding: var(--sp-3); background: rgba(56, 189, 248, 0.08); border-left: 3px solid var(--accent-cyan); border-radius: 4px; font-size: var(--fs-xs); line-height: 1.6;"
          });
          wDetail.appendChild(el("div", { style: "font-weight: 700; font-size: var(--fs-sm); color: var(--accent-cyan); margin-bottom: 2px;", text: selW.word + " (" + selW.lemma + ")" }));
          wDetail.appendChild(el("div", {}, [el("strong", { text: "Part of Speech: " }), document.createTextNode(selW.pos)]));
          wDetail.appendChild(el("div", {}, [el("strong", { text: "Grammatical Parse: " }), document.createTextNode(selW.parse)]));
          wDetail.appendChild(el("div", {}, [el("strong", { text: "Lexical Gloss: " }), document.createTextNode(selW.gloss)]));
          morphCard.appendChild(wDetail);
        } else {
          morphCard.appendChild(el("div", {
            style: "font-size: var(--fs-xs); color: var(--text-dim); font-style: italic;",
            text: "Click any word above to inspect lemma parsing, verbal aspect, and lexical definition."
          }));
        }

        inspectPane.appendChild(morphCard);
      }

      // Card 5: Scholarly Citation Output & Logos / Verbum Export
      var citeCard = el("div", {
        style: "background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--sp-3);"
      });
      var citeHeader = el("div", {
        style: "display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: var(--sp-2);"
      });
      citeHeader.appendChild(el("span", {
        style: "font-size: var(--fs-xs); font-weight: 700; color: var(--text-muted); text-transform: uppercase;",
        text: "Permanent Citation & Logos/Verbum Export"
      }));

      var citeBtnGroup = el("div", { style: "display: flex; gap: var(--sp-2);" });
      var sblCardBtn = el("button", {
        style: "background: var(--bg-panel); color: var(--text-main); border: 1px solid var(--border); border-radius: var(--radius); padding: 3px 8px; font-size: var(--fs-xs); cursor: pointer;",
        text: "📜 Copy SBL",
        on: {
          click: function (e) {
            fetch("/api/manuscripts/cite", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ ms_id: state.selectedMs, folio_id: state.selectedFolio, style: "sbl" })
            })
              .then(function (r) { return r.json(); })
              .then(function (res) {
                copyTextToClipboard(res.sbl, sblCardBtn);
              });
          }
        }
      });
      var logosCardBtn = el("button", {
        style: "background: var(--accent-gold); color: var(--on-gold); border: none; border-radius: var(--radius); padding: 3px 8px; font-size: var(--fs-xs); font-weight: 600; cursor: pointer;",
        text: "📖 Copy Logos/Verbum",
        on: {
          click: function (e) {
            fetch("/api/manuscripts/cite", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ ms_id: state.selectedMs, folio_id: state.selectedFolio, style: "logos_verbum" })
            })
              .then(function (r) { return r.json(); })
              .then(function (res) {
                copyTextToClipboard(res.logos_verbum, logosCardBtn);
              });
          }
        }
      });
      citeBtnGroup.appendChild(sblCardBtn);
      citeBtnGroup.appendChild(logosCardBtn);
      citeHeader.appendChild(citeBtnGroup);
      citeCard.appendChild(citeHeader);

      var citeText = folio.shelfmark + " (" + folio.passage + "), " + state.currentData.manuscript_name + " (" + state.currentData.siglum + "). " +
        (state.currentData.iiif_manifest ? "Facsimile IIIF: " + state.currentData.iiif_manifest : "Digital facsimile: " + state.currentData.viewer_url);
      var citeBox = el("div", {
        style: "font-size: var(--fs-xs); font-family: var(--font-mono); background: var(--bg-base); padding: var(--sp-2); border-radius: 4px; color: var(--accent-gold); word-break: break-all;",
        text: citeText
      });
      citeCard.appendChild(citeBox);
      inspectPane.appendChild(citeCard);
    }

    mainArea.appendChild(inspectPane);
    container.appendChild(mainArea);

    // Initialize 3D WebGL Three.js Scene
    setTimeout(function () {
      initThreeScene(canvasWrap);
    }, 20);
  }

  // ── Dependency Loader: Ensure Three.js and OrbitControls ──────────────────
  function ensureThreeJs(cb) {
    if (window.THREE && window.THREE.OrbitControls) {
      cb();
      return;
    }

    function loadScript(src, next) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = next;
      s.onerror = function () { console.error("Failed to load script:", src); };
      document.head.appendChild(s);
    }

    if (!window.THREE) {
      loadScript("/static/libs/three.min.js", function () {
        if (!window.THREE.OrbitControls) {
          loadScript("/static/libs/OrbitControls.js", cb);
        } else {
          cb();
        }
      });
    } else if (!window.THREE.OrbitControls) {
      loadScript("/static/libs/OrbitControls.js", cb);
    }
  }

  // ── Module Registration ───────────────────────────────────────────────────
  window.JarvisModules.manuscripts = {
    load: function (container) {
      ensureThreeJs(function () {
        fetchManuscripts(function () {
          if (state.manuscripts.length > 0) {
            state.selectedMs = state.manuscripts[0].id;
            fetch("/api/manuscripts/" + encodeURIComponent(state.selectedMs))
              .then(function (r) { return r.json(); })
              .then(function (ms) {
                if (ms && ms.folios && ms.folios.length > 0) {
                  state.selectedFolio = ms.folios[0].id;
                  fetchFolio(state.selectedMs, state.selectedFolio, function () {
                    render(container);
                  });
                } else {
                  render(container);
                }
              });
          } else {
            render(container);
          }
        });
      });
    },
    onShow: function () {
      if (state.containerElem) {
        var vp = document.getElementById("ms-3d-viewport");
        if (vp) initThreeScene(vp);
      }
    }
  };
})();
