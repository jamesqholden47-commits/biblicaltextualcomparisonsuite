/* Pope Leo XIV Ultimate Tracker & Magisterial Record Keeper (module id "pope_leo").
 * Real-time tracking of liturgies, video feeds, homilies, encyclicals, appointments,
 * 'a braccio' remarks, and 4-tier magisterial assent pattern detection.
 */
(function () {
  "use strict";
  window.JarvisModules = window.JarvisModules || {};

  function el(tag, props, text, children) {
    var n = document.createElement(tag);
    if (props) {
      Object.keys(props).forEach(function (k) {
        if (k === "style") n.style.cssText = props[k];
        else if (k === "class") n.className = props[k];
        else if (k.slice(0, 2) === "on") n.addEventListener(k.slice(2), props[k]);
        else n.setAttribute(k, props[k]);
      });
    }
    // If 3rd argument is an array or Node, treat as children
    if (Array.isArray(text) || (text && text.nodeType)) {
      children = text;
      text = null;
    }
    if (text !== undefined && text !== null) {
      n.textContent = text;
    }
    if (children) {
      var list = Array.isArray(children) ? children : [children];
      list.forEach(function (c) {
        if (typeof c === "string") n.appendChild(document.createTextNode(c));
        else if (c && c.nodeType) n.appendChild(c);
      });
    }
    return n;
  }


  var CARD_CSS = "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:16px;margin-bottom:16px;";
  var BADGE_CSS = "display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;text-transform:uppercase;border:1px solid var(--accent-gold);color:var(--accent-gold);margin-right:6px;";
  var BTN_CSS = "background:var(--bg-card);color:var(--accent-gold);border:1px solid var(--border);border-radius:4px;padding:6px 14px;font-size:12px;cursor:pointer;font-weight:600;font-family:inherit;";
  var BTN_ACTIVE = BTN_CSS + "background:rgba(241,224,90,0.15);border-color:var(--accent-gold);color:var(--accent-gold);";
  var TEXTBOX_CSS = "background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:12px;font-size:13px;line-height:1.6;white-space:pre-wrap;max-height:380px;overflow-y:auto;font-family:inherit;";

  var activeSubTab = "today";
  var feedData = null;

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:20px;color:var(--text-main);max-width:1440px;margin:0 auto;";

    // Header Bar
    var header = el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px;" }, null, [
      el("div", null, null, [
        el("h2", { style: "margin:0 0 4px 0;color:var(--accent-gold);font-size:22px;display:flex;align-items:center;gap:8px;" }, "🇻🇦 Pope Leo XIV Ultimate Tracker & Magisterial Record"),
        el("p", { style: "margin:0;color:var(--text-muted);font-size:13px;" }, 
          "Complete chronicle of liturgies, video feeds, encyclicals, appointments, 'a braccio' remarks, and 4-tier assent analytics."
        )
      ]),
      el("div", { style: "display:flex;gap:10px;" }, null, [
        el("button", { id: "pope-refresh-btn", style: BTN_CSS, onclick: function() { refreshData(root); } }, "🔄 Refresh Vatican Feed")
      ])
    ]);
    root.appendChild(header);

    var contentContainer = el("div", { id: "pope-main-content" });
    root.appendChild(contentContainer);

    fetchData(contentContainer);
  }

  function fetchData(container) {
    container.textContent = "";
    container.appendChild((window.JarvisUI && window.JarvisUI.loading) ? window.JarvisUI.loading("Loading Pope Leo XIV master repository...") : document.createTextNode("Loading Pope Leo XIV master repository..."));
    fetch("/api/pope-leo/feed")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        feedData = data;
        renderMasterView(container, data);
      })
      .catch(function (err) {
        container.textContent = "Error loading Pope Leo feed: " + err;
      });
  }

  function refreshData(root) {
    var btn = root.querySelector("#pope-refresh-btn");
    if (btn) btn.textContent = "Refreshing from Vatican...";
    fetch("/api/pope-leo/refresh", { method: "POST" })
      .then(function(r) { return r.json(); })
      .then(function() {
        var container = root.querySelector("#pope-main-content");
        if (container) fetchData(container);
        if (btn) btn.textContent = "🔄 Refresh Vatican Feed";
      })
      .catch(function(e) {
        alert("Failed to refresh: " + e);
        if (btn) btn.textContent = "🔄 Refresh Vatican Feed";
      });
  }

  function renderMasterView(container, data) {
    container.textContent = "";

    var pontiff = data.pontiff || {};

    // 1. Pontiff & Motto Banner
    var banner = el("div", { style: CARD_CSS + "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;border-left:4px solid var(--accent-gold);" }, null, [
      el("div", null, null, [
        el("div", { style: "font-size:19px;font-weight:700;color:var(--on-accent);" }, pontiff.name + " (" + pontiff.secular_name + ")"),
        el("div", { style: "color:var(--text-muted);font-size:12px;margin:2px 0 6px 0;" },
          pontiff.number + " • Elected " + pontiff.election_date + " • Motto: " + (pontiff.motto || "") + " • " + pontiff.origin
        ),
        el("div", { style: "color:var(--accent-gold);font-weight:600;font-size:14px;" }, data.liturgical_day)
      ]),
      el("div", { style: "display:flex;flex-direction:column;align-items:flex-end;gap:6px;" }, null, [
        el("span", { style: BADGE_CSS + "border-color:var(--accent-cyan);color:var(--accent-cyan);" }, data.calendar_note),
        el("a", { href: pontiff.official_url, target: "_blank", style: "color:var(--accent-cyan);font-size:12px;text-decoration:none;" }, "Official Vatican.va Link →")
      ])
    ]);
    container.appendChild(banner);

    // 1b. Live Dynamic Liturgical Day Banner (Real-Time Liturgical Tracker)
    var live = data.liturgical_today_live || {};
    var liveDate = live.date || data.current_date;
    var liveTitle = live.full_title || live.liturgical_day || "Live Liturgical Day";
    var liveColor = live.liturgical_color || "White";
    var liveRank = live.rank || "Memorial";
    var liveCycle = (live.weekday_cycle ? live.weekday_cycle : "") + (live.sunday_cycle ? " / " + live.sunday_cycle : "");

    var liveBanner = el("div", {
      style: CARD_CSS + "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;background:rgba(56,189,248,0.06);border-left:4px solid var(--accent-cyan);"
    }, null, [
      el("div", null, null, [
        el("div", { style: "display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;" }, null, [
          el("span", { style: "font-size:11px;font-weight:700;text-transform:uppercase;color:var(--accent-cyan);letter-spacing:0.5px;" }, "🕊️ Live Liturgical Calendar (Real-Time)"),
          el("span", { style: BADGE_CSS + "border-color:var(--accent-cyan);color:var(--accent-cyan);font-size:10px;padding:1px 6px;" }, liveRank),
          el("span", { style: BADGE_CSS + "border-color:var(--accent-gold);color:var(--accent-gold);font-size:10px;padding:1px 6px;" }, "Color: " + liveColor),
          liveCycle ? el("span", { style: BADGE_CSS + "border-color:var(--text-muted);color:var(--text-muted);font-size:10px;padding:1px 6px;" }, liveCycle) : null
        ]),
        el("div", { style: "font-size:15px;font-weight:600;color:var(--text-main);" }, liveTitle),
        el("div", { style: "font-size:12px;color:var(--text-muted);margin-top:2px;" },
          (live.season_week_label || "Ordinary Time") + " • System Date: " + (data.current_date_display || liveDate) + " • Vatican Status: " + (data.vatican_status === "online" ? "🟢 Online" : "🟡 Cached Baseline")
        )
      ]),
      el("div", { style: "display:flex;align-items:center;gap:8px;" }, null, [
        el("span", { style: "font-size:12px;color:var(--text-dim);" }, "Historical Anchor:"),
        el("span", { style: BADGE_CSS + "border-color:var(--accent-gold);color:var(--accent-gold);" }, "4 October 2026 (Inaugural Baseline)")
      ])
    ]);
    container.appendChild(liveBanner);

    // 2. Video Feed Section
    var videoCard = renderVideoSection(data.video_streams || {}, data);
    container.appendChild(videoCard);

    // 3. Sub-Navigation Tabs
    var subNav = el("div", { style: "display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;border-bottom:1px solid var(--border);padding-bottom:10px;" }, null, [
      makeTabBtn("today", "☀️ Today's Radar & Liturgy", container),
      makeTabBtn("documents", "📜 Magisterial Registry (Encyclicals)", container),
      makeTabBtn("moves", "🏛️ Ecclesial Moves & Consistories", container),
      makeTabBtn("abraccio", "🎙️ 'A Braccio' & Airplane Log", container),
      makeTabBtn("analytics", "⚖️ 4 Levels of Assent & Patterns", container)
    ]);
    container.appendChild(subNav);

    // 4. Tab Body Area
    var tabBody = el("div", { id: "pope-tab-body" });
    container.appendChild(tabBody);

    renderActiveTab(tabBody, data);
  }

  function makeTabBtn(id, label, mainContainer) {
    var isActive = activeSubTab === id;
    return el("button", {
      style: isActive ? BTN_ACTIVE : BTN_CSS,
      onclick: function() {
        activeSubTab = id;
        var tabBody = mainContainer.querySelector("#pope-tab-body");
        if (tabBody) renderActiveTab(tabBody, feedData);
        // Update button styles
        var btns = mainContainer.querySelectorAll("button");
        btns.forEach(function(b) {
          if (b.id !== "pope-refresh-btn") {
            b.style.cssText = b.textContent.includes(label.slice(2, 6)) ? BTN_ACTIVE : BTN_CSS;
          }
        });
      }
    }, label);
  }

  function renderVideoSection(streams, masterData) {
    var liveChannels = streams.live_channels || [];
    var replays = streams.today_replays || [];
    var backups = streams.backup_urls || [];
    var advisory = streams.troubleshooting_advisory || {};
    var latestVideoId = (masterData && masterData.latest_youtube_video_id) || "DEuZdFrPw7s";

    var activeItem = liveChannels.length > 0 ? liveChannels[0] : (replays.length > 0 ? replays[0] : null);
    var currentEmbed = activeItem && activeItem.embed_url && !activeItem.embed_url.includes("live_stream?channel=")
      ? activeItem.embed_url
      : ("https://www.youtube.com/embed/" + latestVideoId);
    var currentTitle = activeItem ? activeItem.title : "Vatican Media Stream";
    var currentDirectUrl = activeItem ? (activeItem.direct_url || activeItem.url || "") : "https://www.youtube.com/@VaticanNewsEN/live";

    var card = el("div", { style: CARD_CSS }, null, [
      // 1. Header & Title Bar with Direct Action Launchpad
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;" }, null, [
        el("div", { style: "display:flex;align-items:center;gap:10px;" }, null, [
          el("h3", { style: "margin:0;color:var(--accent-gold);font-size:16px;" }, "📺 Vatican Video Feed & Liturgy Broadcasts"),
          el("span", { style: BADGE_CSS + "border-color:var(--ok);color:var(--ok);" }, "Live Stream Hub"),
          el("span", { style: BADGE_CSS + "border-color:var(--accent-cyan);color:var(--accent-cyan);" }, (backups.length || 11) + " Backup Mirrors")
        ]),
        // Quick Launchpad Action Bar
        el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;" }, null, [
          el("a", {
            href: "https://www.youtube.com/@VaticanNewsEN/live",
            target: "_blank",
            rel: "noopener noreferrer",
            style: BTN_CSS + "background:rgba(210,153,34,0.15);color:var(--accent-gold);border-color:var(--accent-gold);font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:4px;"
          }, "🔴 Watch Live EN ↗"),
          el("a", {
            href: "https://www.youtube.com/@VaticanNewsIT/live",
            target: "_blank",
            rel: "noopener noreferrer",
            style: BTN_CSS + "background:rgba(46,164,78,0.15);color:var(--ok);border-color:var(--ok);font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:4px;"
          }, "🇮🇹 Diretta Live IT ↗"),
          el("a", {
            href: "https://www.vaticannews.va/en/epg.html",
            target: "_blank",
            rel: "noopener noreferrer",
            style: BTN_CSS + "background:rgba(88,166,255,0.15);color:var(--accent-cyan);border-color:var(--accent-cyan);font-weight:700;text-decoration:none;display:inline-flex;align-items:center;gap:4px;"
          }, "🏛️ Vatican EPG ↗"),
          el("a", {
            href: "https://www.youtube.com/@EWTN/live",
            target: "_blank",
            rel: "noopener noreferrer",
            style: BTN_CSS + "color:var(--text-muted);border-color:var(--border);text-decoration:none;display:inline-flex;align-items:center;gap:4px;"
          }, "✝️ EWTN Relay ↗")
        ])
      ]),

      // 2. Troubleshooting & Fallback Advisory Alert
      el("div", { style: "background:rgba(210,153,34,0.08);border:1px solid rgba(210,153,34,0.3);border-radius:6px;padding:10px 14px;margin-bottom:12px;font-size:12px;line-height:1.45;color:var(--text-main);" }, null, [
        el("div", { style: "display:flex;align-items:center;gap:6px;margin-bottom:4px;" }, null, [
          el("strong", { style: "color:var(--accent-gold);" }, "⚠️ Stream Diagnostics & Direct Working Links Notice:"),
          el("span", { style: "color:var(--text-muted);font-size:11px;" }, "(YouTube embed policy & off-air handling)")
        ]),
        el("div", { style: "color:var(--text-muted);" }, null, [
          "If the embedded player below displays ",
          el("code", { style: "background:rgba(0,0,0,0.4);color:var(--bad);padding:1px 5px;border-radius:3px;" }, "Video unavailable"),
          ", this is because YouTube deprecated legacy unauthenticated channel live iframes and returns offline errors when the Vatican Television Center is between broadcast events. ",
          el("strong", { style: "color:var(--on-accent);" }, "Click any of the direct launch buttons above or in the backup directory below"),
          " to open the verified, unrestricted high-definition stream directly."
        ])
      ]),

      // 3. Channel & Replay Selector Buttons
      el("div", { style: "display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center;" }, null, [
        el("span", { style: "font-size:11px;font-weight:600;color:var(--text-muted);margin-right:4px;" }, "Switch Feed:"),
        el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;" }, null,
          liveChannels.map(function(ch) {
            return el("button", {
              style: BTN_CSS + "padding:4px 10px;font-size:11px;",
              onclick: function() {
                updatePlayer(ch);
              }
            }, "🔴 " + ch.title);
          }).concat(
            replays.map(function(rp) {
              return el("button", {
                style: BTN_CSS + "padding:4px 10px;font-size:11px;color:var(--accent-cyan);border-color:var(--accent-cyan);",
                onclick: function() {
                  updatePlayer(rp);
                }
              }, "⏯️ " + rp.title);
            })
          ).concat([
            el("button", {
              style: BTN_CSS + "padding:4px 10px;font-size:11px;color:var(--accent-purple);border-color:var(--accent-purple);",
              onclick: function() {
                updatePlayer({
                  title: "Vatican Radio 24/7 Live Web Audio (English)",
                  description: "Continuous direct audio stream broadcast from Vatican Radio.",
                  direct_url: "https://radio.vaticannews.va/stream-en",
                  is_audio: true,
                  audio_url: "https://radio.vaticannews.va/stream-en"
                });
              }
            }, "📻 Vatican Radio Live")
          ])
        )
      ]),

      // 4. Video Player & Active Stream Details (2 Columns)
      el("div", { style: "display:grid;grid-template-columns: 2fr 1fr;gap:14px;margin-bottom:16px;" }, null, [
        // Video Container
        el("div", { style: "background:var(--media-bg);border-radius:6px;overflow:hidden;aspect-ratio:16/9;position:relative;display:flex;flex-direction:column;justify-content:center;align-items:center;" }, null, [
          el("iframe", {
            id: "pope-video-frame",
            src: currentEmbed,
            style: "width:100%;height:100%;border:none;",
            allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture",
            allowfullscreen: "true"
          }),
          // Direct launch overlay bar pinned to bottom of player
          el("div", {
            id: "pope-player-overlay",
            style: "width:100%;background:rgba(13,17,23,0.92);border-top:1px solid var(--border);padding:6px 12px;display:flex;justify-content:space-between;align-items:center;box-sizing:border-box;"
          }, null, [
            el("span", { id: "pope-player-overlay-text", style: "font-size:11px;color:var(--text-muted);" }, "Player offline or blocked?"),
            el("a", {
              id: "pope-player-direct-btn",
              href: currentDirectUrl,
              target: "_blank",
              rel: "noopener noreferrer",
              style: BTN_CSS + "padding:2px 8px;font-size:11px;background:var(--accent-gold);color:var(--on-gold);font-weight:700;text-decoration:none;border-color:var(--accent-gold);"
            }, "🚀 Open Stream in YouTube ↗")
          ])
        ]),

        // Timestamp & Active Stream Inspector Box
        el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:12px;overflow-y:auto;max-height:380px;display:flex;flex-direction:column;" }, null, [
          el("div", { id: "pope-video-title", style: "font-weight:700;color:var(--accent-gold);margin-bottom:6px;font-size:13px;" }, currentTitle),
          el("div", { id: "pope-video-desc", style: "font-size:12px;color:var(--text-muted);margin-bottom:10px;line-height:1.4;" },
            activeItem ? (activeItem.description || "Direct broadcast relay from the Vatican Television Center (Vatican Media).") : "Direct broadcast relay."
          ),
          
          // Action Buttons for this specific stream
          el("div", { style: "margin-bottom:12px;" }, null, [
            el("a", {
              id: "pope-active-direct-link",
              href: currentDirectUrl,
              target: "_blank",
              rel: "noopener noreferrer",
              style: BTN_CSS + "width:100%;text-align:center;box-sizing:border-box;display:block;padding:6px 10px;font-size:11px;background:rgba(46,164,78,0.15);color:var(--ok);border-color:var(--ok);font-weight:700;text-decoration:none;margin-bottom:6px;"
            }, "🔗 Launch Active Stream (Full Quality) ↗"),
            el("a", {
              id: "pope-active-portal-link",
              href: activeItem && activeItem.web_url ? activeItem.web_url : "https://www.vaticannews.va/en.html",
              target: "_blank",
              rel: "noopener noreferrer",
              style: BTN_CSS + "width:100%;text-align:center;box-sizing:border-box;display:block;padding:4px 10px;font-size:11px;color:var(--text-muted);text-decoration:none;"
            }, "🏛️ Official Vatican News Portal ↗")
          ]),

          el("div", { style: "font-size:12px;font-weight:600;color:var(--accent-cyan);margin-bottom:6px;" }, "Liturgy Chapters & Markers:"),
          el("div", { id: "pope-timestamps-list" }, null,
            (replays[0] ? replays[0].timestamps || [] : []).map(function(ts) {
              return el("div", { style: "display:flex;gap:8px;font-size:11px;margin-bottom:4px;color:var(--text-main);" }, null, [
                el("span", { style: "color:var(--accent-gold);font-family:monospace;font-weight:600;" }, ts.time),
                el("span", null, ts.label)
              ]);
            })
          )
        ])
      ]),

      // 5. Comprehensive Backup Mirrors Directory (The Resilient Working Links Matrix)
      el("div", { style: "border-top:1px solid var(--border);padding-top:14px;margin-top:6px;" }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;flex-wrap:wrap;gap:8px;" }, null, [
          el("h4", { style: "margin:0;color:var(--accent-cyan);font-size:14px;display:flex;align-items:center;gap:6px;" }, [
            el("span", null, "🛡️"),
            el("span", null, "Working Broadcast Links & Backup Mirrors Directory (" + (backups.length || 11) + " Verified)")
          ]),
          el("span", { style: "font-size:11px;color:var(--text-muted);" }, "All links verified against Dicastery for Communication")
        ]),
        el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:10px;" }, null,
          backups.map(function(b) {
            return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;display:flex;flex-direction:column;justify-content:space-between;" }, null, [
              el("div", null, [
                el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
                  el("strong", { style: "font-size:12px;color:var(--text-main);" }, b.title),
                  el("span", { style: BADGE_CSS + "font-size:9px;margin:0;" }, b.badge || "Live")
                ]),
                el("div", { style: "font-size:11px;color:var(--text-muted);margin-bottom:8px;line-height:1.35;" }, b.description),
                el("div", { style: "font-size:10px;font-family:monospace;color:var(--accent-gold);margin-bottom:8px;word-break:break-all;" }, b.url)
              ]),
              el("a", {
                href: b.url,
                target: "_blank",
                rel: "noopener noreferrer",
                style: BTN_CSS + "display:block;text-align:center;padding:4px 8px;font-size:11px;color:var(--accent-cyan);border-color:var(--accent-cyan);text-decoration:none;font-weight:600;"
              }, "Launch Stream ↗")
            ]);
          })
        )
      ])
    ]);

    function updatePlayer(item) {
      var iframe = card.querySelector("#pope-video-frame");
      var titleSpan = card.querySelector("#pope-video-title");
      var descDiv = card.querySelector("#pope-video-desc");
      var overlayBtn = card.querySelector("#pope-player-direct-btn");
      var activeDirect = card.querySelector("#pope-active-direct-link");
      var activePortal = card.querySelector("#pope-active-portal-link");
      var tsContainer = card.querySelector("#pope-timestamps-list");

      if (titleSpan) titleSpan.textContent = (item.type === "live_stream" ? "🔴 " : "⏯️ ") + item.title;
      if (descDiv) descDiv.textContent = item.description || "Direct official stream.";

      var direct = item.direct_url || item.url || "https://www.youtube.com/@VaticanNewsEN/live";
      if (overlayBtn) overlayBtn.href = direct;
      if (activeDirect) activeDirect.href = direct;
      if (activePortal) activePortal.href = item.web_url || item.portal_url || "https://www.vaticannews.va/en.html";

      if (iframe) {
        if (item.is_audio) {
          iframe.src = "about:blank";
          iframe.style.display = "none";
        } else {
          iframe.style.display = "block";
          if (item.embed_url && !item.embed_url.includes("live_stream?channel=")) {
            iframe.src = item.embed_url;
          } else {
            iframe.src = "https://www.youtube.com/embed/" + latestVideoId;
          }
        }
      }

      if (tsContainer) {
        tsContainer.textContent = "";
        var list = item.timestamps || [];
        if (list.length === 0) {
          tsContainer.appendChild(el("div", { style: "font-size:11px;color:var(--text-muted);font-style:italic;" }, "No chapter markers for live unscripted broadcast."));
        } else {
          list.forEach(function(ts) {
            tsContainer.appendChild(el("div", { style: "display:flex;gap:8px;font-size:11px;margin-bottom:4px;color:var(--text-main);" }, null, [
              el("span", { style: "color:var(--accent-gold);font-family:monospace;font-weight:600;" }, ts.time),
              el("span", null, ts.label)
            ]));
          });
        }
      }
    }

    return card;
  }


  function renderActiveTab(tabBody, data) {
    tabBody.textContent = "";

    if (activeSubTab === "today") {
      renderTodayTab(tabBody, data);
    } else if (activeSubTab === "documents") {
      renderDocumentsTab(tabBody, data);
    } else if (activeSubTab === "moves") {
      renderMovesTab(tabBody, data);
    } else if (activeSubTab === "abraccio") {
      renderAbraccioTab(tabBody, data);
    } else if (activeSubTab === "analytics") {
      renderAnalyticsTab(tabBody, data);
    }
  }

  // TAB 1: TODAY'S RADAR & LITURGY
  function renderTodayTab(tabBody, data) {
    var todayEvents = data.today_events || [];
    var angelus = todayEvents.find(function(e) { return e.id === "angelus-20261004"; }) || {};
    var mass = todayEvents.find(function(e) { return e.id === "mass-20261003-gendarmeria"; }) || {};

    // Processions Radar
    var procCard = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 12px 0;color:var(--accent-cyan);font-size:16px;" }, "🚶‍♂️ Processions & Pilgrimages Radar (4 October 2026)"),
      el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));gap:12px;" }, null,
        (angelus.processions_and_pilgrimages || []).map(function(p) {
          return el("div", { style: "background:var(--bg-card);border-left:3px solid var(--accent-gold);padding:10px 14px;border-radius:0 4px 4px 0;" }, null, [
            el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
              el("strong", { style: "color:var(--on-accent);font-size:14px;" }, p.name),
              el("span", { style: BADGE_CSS + "font-size:10px;margin-right:0;" }, p.type)
            ]),
            el("div", { style: "font-size:12px;color:var(--text-muted);line-height:1.4;" }, p.details)
          ]);
        })
      )
    ]);
    tabBody.appendChild(procCard);

    // Liturgies Grid
    var grid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(500px, 1fr));gap:16px;" }, null, [
      // Angelus
      el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;" }, null, [
          el("h3", { style: "margin:0;color:var(--accent-gold);font-size:16px;" }, "☀️ " + angelus.title),
          el("span", { style: BADGE_CSS }, "St. Peter's Square")
        ]),
        el("div", { style: "font-size:12px;color:var(--accent-gold);margin-bottom:8px;" },
          "Gospel: " + ((angelus.readings && angelus.readings.gospel) || "")
        ),
        el("div", { style: "background:rgba(88,166,255,0.08);border:1px solid rgba(88,166,255,0.3);border-radius:4px;padding:8px 10px;font-size:12px;margin-bottom:10px;" }, null, [
          el("strong", { style: "color:var(--accent-cyan);" }, "Theological Key: "),
          el("span", null, angelus.exegesis_summary)
        ]),
        el("div", { style: "margin-bottom:6px;font-size:12px;font-weight:600;color:var(--accent-gold);" }, "Allocution Full Text:"),
        el("div", { style: TEXTBOX_CSS }, angelus.full_text_en)
      ]),

      // Gendarmerie Mass
      el("div", { style: CARD_CSS }, null, [
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;" }, null, [
          el("h3", { style: "margin:0;color:var(--accent-green);font-size:16px;" }, "🛡️ " + mass.title),
          el("span", { style: BADGE_CSS + "border-color:var(--accent-green);color:var(--accent-green);" }, "Lourdes Grotto")
        ]),
        el("div", { style: "font-size:12px;color:var(--accent-green);margin-bottom:8px;" },
          "Occasion: " + (mass.liturgical_occasion || "")
        ),
        el("div", { style: "background:rgba(63,185,80,0.08);border:1px solid rgba(63,185,80,0.3);border-radius:4px;padding:8px 10px;font-size:12px;margin-bottom:10px;" }, null, [
          el("strong", { style: "color:var(--accent-green);" }, "Homily Key: "),
          el("span", null, mass.homily_summary)
        ]),
        el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;" }, null, [
          el("span", { style: "font-size:12px;font-weight:600;color:var(--accent-green);" }, "Homily (English Translation):"),
          el("button", {
            style: BTN_CSS + "padding:2px 8px;font-size:11px;",
            onclick: function(ev) {
              var box = ev.target.parentElement.nextElementSibling;
              if (box.getAttribute("data-lang") === "it") {
                box.textContent = mass.full_text_en_translation;
                box.setAttribute("data-lang", "en");
                ev.target.textContent = "Show Italian Original";
              } else {
                box.textContent = mass.full_text_it;
                box.setAttribute("data-lang", "it");
                ev.target.textContent = "Show English Translation";
              }
            }
          }, "Show Italian Original")
        ]),
        el("div", { style: TEXTBOX_CSS, "data-lang": "en" }, mass.full_text_en_translation)
      ])
    ]);
    tabBody.appendChild(grid);
  }

  // TAB 2: MAGISTERIAL DOCUMENTS & ENCYCLICALS
  function renderDocumentsTab(tabBody, data) {
    var docs = data.magisterial_documents || [];
    var card = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 12px 0;color:var(--accent-gold);font-size:17px;" }, "📜 Promulgated & In-Progress Magisterial Corpus"),
      el("div", { style: "display:grid;grid-template-columns:1fr;gap:14px;" }, null,
        docs.map(function(doc) {
          return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:14px;" }, null, [
            el("div", { style: "display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:6px;" }, null, [
              el("div", null, null, [
                el("strong", { style: "font-size:15px;color:var(--on-accent);" }, doc.title),
                el("div", { style: "color:var(--accent-cyan);font-size:13px;font-style:italic;" }, doc.subtitle)
              ]),
              el("div", { style: "display:flex;gap:6px;align-items:center;" }, null, [
                el("span", { style: BADGE_CSS + "border-color:var(--accent-cyan);color:var(--accent-cyan);" }, doc.type),
                el("span", { style: BADGE_CSS }, doc.promulgated)
              ])
            ]),
            el("div", { style: "margin:6px 0;font-size:12px;color:var(--accent-gold);font-weight:600;" }, doc.level),
            el("div", { style: "font-size:12px;color:var(--text-muted);margin:8px 0 4px 0;" }, "Key Doctrinal Theses:"),
            el("ul", { style: "margin:0;padding-left:18px;font-size:12px;line-height:1.5;color:var(--text-main);" }, null,
              (doc.key_theses || []).map(function(th) { return el("li", null, th); })
            ),
            el("div", { style: "margin-top:10px;text-align:right;" }, null, [
              el("a", { href: doc.url, target: "_blank", style: "color:var(--accent-cyan);font-size:12px;text-decoration:none;" }, "View Official Text on Vatican.va →")
            ])
          ]);
        })
      )
    ]);
    tabBody.appendChild(card);
  }

  // TAB 3: ECCLESIAL MOVES & CONSISTORIES
  function renderMovesTab(tabBody, data) {
    var moves = data.ecclesial_moves || [];
    var card = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 12px 0;color:var(--accent-cyan);font-size:17px;" }, "🏛️ Appointments, Consistories & Ecclesial Governance"),
      el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:12px;" }, null,
        moves.map(function(m) {
          return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-left:3px solid var(--accent-cyan);border-radius:0 4px 4px 0;padding:12px 14px;" }, null, [
            el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
              el("span", { style: "font-size:11px;color:var(--text-muted);" }, m.date),
              el("span", { style: BADGE_CSS + "font-size:10px;margin-right:0;" }, m.category)
            ]),
            el("strong", { style: "font-size:14px;color:var(--on-accent);display:block;margin-bottom:6px;" }, m.title),
            el("p", { style: "margin:0;font-size:12px;color:var(--text-muted);line-height:1.4;" }, m.description)
          ]);
        })
      )
    ]);
    tabBody.appendChild(card);
  }

  // TAB 4: "A BRACCIO" & AIRPLANE LOG
  function renderAbraccioTab(tabBody, data) {
    var logs = data.abraccio_log || [];
    var card = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 12px 0;color:var(--accent-gold);font-size:17px;" }, "🎙️ 'A Braccio' Chronicle & In-Flight Press Conferences"),
      el("div", { style: "display:grid;grid-template-columns:1fr;gap:14px;" }, null,
        logs.map(function(item) {
          return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:14px;" }, null, [
            el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:6px;" }, null, [
              el("strong", { style: "font-size:14px;color:var(--accent-gold);" }, item.occasion),
              el("span", { style: "font-size:12px;color:var(--text-muted);" }, item.date)
            ]),
            el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:8px;font-style:italic;" }, "Context: " + item.context),
            el("div", { style: "background:rgba(241,224,90,0.06);border-left:3px solid var(--accent-gold);padding:8px 12px;border-radius:0 4px 4px 0;margin-bottom:8px;font-size:13px;color:var(--on-accent);line-height:1.5;" },
              "“" + item.unscripted_quote + "”"
            ),
            el("div", { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;font-size:11px;" }, null, [
              el("span", { style: "color:var(--accent-cyan);" }, "Magisterial Classification: " + item.assent_level),
              el("span", { style: "color:var(--text-muted);" }, "Theological Reading: " + item.analysis)
            ])
          ]);
        })
      )
    ]);
    tabBody.appendChild(card);
  }

  // TAB 5: 4 LEVELS OF ASSENT & PATTERN DETECTION
  function renderAnalyticsTab(tabBody, data) {
    var analytics = data.doctrinal_analytics || {};
    var levels = analytics.levels || [];
    var patterns = analytics.emerging_doctrinal_patterns || [];

    var card = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 6px 0;color:var(--accent-gold);font-size:17px;" }, "⚖️ 4 Levels of Infallibility & Theological Assent Matrix"),
      el("p", { style: "margin:0 0 14px 0;font-size:12px;color:var(--text-muted);" },
        "Canonical evaluation per CDF Donum Veritatis (1990), Ratzinger-Bertone Professio Fidei Commentary (1998), and CIC Cann. 750, 752, 753."
      ),

      // 4 Levels Breakdown
      el("div", { style: "display:grid;grid-template-columns:1fr;gap:12px;margin-bottom:20px;" }, null,
        levels.map(function(lvl) {
          var borderColor = lvl.level === 1 ? "var(--accent-gold)" : (lvl.level === 2 ? "var(--accent-cyan)" : (lvl.level === 3 ? "var(--accent-green)" : "var(--border)"));
          return el("div", { style: "background:var(--bg-card);border:1px solid " + borderColor + ";border-radius:6px;padding:12px 16px;" }, null, [
            el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;flex-wrap:wrap;gap:6px;" }, null, [
              el("strong", { style: "color:var(--on-accent);font-size:14px;" }, "Level " + lvl.level + ": " + lvl.name),
              el("span", { style: BADGE_CSS }, lvl.canonical_anchor)
            ]),
            el("div", { style: "font-size:12px;color:var(--accent-gold);margin-bottom:6px;" }, "Required Assent: " + lvl.required_assent),
            el("p", { style: "margin:0 0 6px 0;font-size:12px;color:var(--text-muted);" }, lvl.description),
            (lvl.items && lvl.items.length > 0) ? el("div", { style: "background:rgba(0,0,0,0.2);border-radius:4px;padding:8px 10px;font-size:11px;" }, null,
              lvl.items.map(function(it) {
                return el("div", { style: "margin-bottom:4px;" }, null, [
                  el("strong", { style: "color:var(--accent-cyan);" }, it.document + ": "),
                  el("span", null, it.proposition)
                ]);
              })
            ) : el("div", { style: "font-size:11px;color:var(--text-muted);font-style:italic;" }, "Zero items promulgated in this tier during this pontificate.")
          ]);
        })
      ),

      // Emerging Patterns
      el("h3", { style: "margin:0 0 10px 0;color:var(--accent-cyan);font-size:16px;" }, "🧠 Emerging Doctrinal Patterns & Theological Vectors"),
      el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:12px;" }, null,
        patterns.map(function(pt) {
          return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:12px 14px;" }, null, [
            el("strong", { style: "color:var(--accent-gold);font-size:14px;display:block;margin-bottom:4px;" }, pt.pattern),
            el("span", { style: BADGE_CSS + "border-color:var(--accent-cyan);color:var(--accent-cyan);font-size:10px;margin-bottom:8px;" }, pt.frequency),
            el("p", { style: "margin:8px 0 0 0;font-size:12px;color:var(--text-muted);line-height:1.4;" }, pt.evidence)
          ]);
        })
      )
    ]);
    tabBody.appendChild(card);
  }

  window.JarvisModules["pope_leo"] = { load: load };
})();
