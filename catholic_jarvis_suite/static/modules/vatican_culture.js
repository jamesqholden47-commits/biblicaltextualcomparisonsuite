/* Vatican Curial Intel, Religious Orders & Scholarly Journals Portal (module id "vatican_culture").
 * Deep dive into Roman intellectual life, pontifical universities, religious orders,
 * scholarly journals (Civiltà Cattolica, Revue Thomiste, Revue Bénédictine, Analecta Bollandiana),
 * the curial bookshelf, and high-priority theological debates.
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

  var activeCultureTab = "orders";
  var cultureData = null;
  var journalFilter = "all";
  var journalSearch = "";

  function load(root) {
    root.textContent = "";
    root.style.cssText = "padding:20px;color:var(--text-main);max-width:1440px;margin:0 auto;";

    // Header Bar
    var header = el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:12px;" }, null, [
      el("div", null, null, [
        el("h2", { style: "margin:0 0 4px 0;color:var(--accent-gold);font-size:22px;display:flex;align-items:center;gap:8px;" }, "🏛️ Vatican Intel & Curial Culture Portal"),
        el("p", { style: "margin:0;color:var(--text-muted);font-size:13px;" }, 
          "The Living Intellectual Operating System of Rome: Religious Orders, Pontifical Faculties, Scholarly Journals & Curial Debates."
        )
      ]),
      el("div", { style: "display:flex;gap:8px;" }, null, [
        el("a", {
          href: "https://www.vatican.va",
          target: "_blank",
          rel: "noopener noreferrer",
          style: BTN_CSS + "text-decoration:none;display:inline-flex;align-items:center;gap:4px;"
        }, "🇻🇦 Holy See Portal ↗"),
        el("a", {
          href: "https://www.laciviltacattolica.it",
          target: "_blank",
          rel: "noopener noreferrer",
          style: BTN_CSS + "color:var(--accent-cyan);border-color:var(--accent-cyan);text-decoration:none;display:inline-flex;align-items:center;gap:4px;"
        }, "📖 Civiltà Cattolica ↗")
      ])
    ]);
    root.appendChild(header);

    var contentContainer = el("div", { id: "vatican-culture-main" });
    root.appendChild(contentContainer);

    fetchData(contentContainer);
  }

  function fetchData(container) {
    container.textContent = "Loading Vatican intellectual culture and journals repository...";
    fetch("/api/vatican-culture/all")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        cultureData = data;
        renderMain(container, data);
      })
      .catch(function (err) {
        container.textContent = "Error loading Vatican Culture data: " + err;
      });
  }

  function renderMain(container, data) {
    container.textContent = "";

    // Stats Bar
    var counts = {
      orders: (data.orders || []).length,
      journals: (data.journals || []).length,
      bookshelf: (data.curial_bookshelf || []).length,
      debates: (data.curial_debates || []).length,
      news: (data.curial_news_feed || []).length
    };

    var statsCard = el("div", { style: "background:rgba(210,153,34,0.06);border:1px solid rgba(210,153,34,0.25);border-radius:6px;padding:10px 16px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;" }, null, [
      el("div", { style: "display:flex;align-items:center;gap:12px;flex-wrap:wrap;" }, null, [
        el("span", { style: BADGE_CSS + "border-color:var(--ok);color:var(--ok);" }, "Pontificate: Leo XIV (O.S.A.)"),
        el("span", { style: "font-size:12px;color:var(--text-muted);" }, 
          counts.orders + " Major Orders · " + counts.journals + " Scholarly Journals · " + counts.bookshelf + " Books on Curial Desks · " + counts.debates + " Doctrinal Vectors"
        )
      ]),
      el("div", { style: "font-size:11px;color:var(--accent-cyan);font-weight:600;" }, "Rome · Holy See Academic Ecosystem")
    ]);
    container.appendChild(statsCard);

    // Subtab Navigation
    var navBar = el("div", { style: "display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;border-bottom:1px solid var(--border);padding-bottom:10px;" }, null, [
      createSubTabBtn("orders", "🏛️ Religious Orders & Roman Seats", container, data),
      createSubTabBtn("journals", "📚 Scholarly Journals & Gazettes (" + counts.journals + ")", container, data),
      createSubTabBtn("bookshelf", "🧠 Curial Bookshelf & Debates (" + counts.debates + ")", container, data),
      createSubTabBtn("intel_feed", "📰 Live Curial Dispatches (" + counts.news + ")", container, data)
    ]);
    container.appendChild(navBar);

    var tabBody = el("div", { id: "culture-tab-body" });
    container.appendChild(tabBody);

    renderActiveTab(tabBody, data);
  }

  function createSubTabBtn(id, label, container, data) {
    return el("button", {
      style: activeCultureTab === id ? BTN_ACTIVE : BTN_CSS,
      onclick: function () {
        activeCultureTab = id;
        var btns = container.querySelectorAll("button");
        btns.forEach(function (b) {
          if (b.textContent.includes(label.slice(2, 6))) b.style.cssText = BTN_ACTIVE;
          else if (b.textContent.includes("🏛️") || b.textContent.includes("📚") || b.textContent.includes("🧠") || b.textContent.includes("📰")) {
            b.style.cssText = BTN_CSS;
          }
        });
        var tabBody = container.querySelector("#culture-tab-body");
        if (tabBody) renderActiveTab(tabBody, data);
      }
    }, label);
  }

  function renderActiveTab(tabBody, data) {
    tabBody.textContent = "";
    if (activeCultureTab === "orders") renderOrdersTab(tabBody, data);
    else if (activeCultureTab === "journals") renderJournalsTab(tabBody, data);
    else if (activeCultureTab === "bookshelf") renderBookshelfTab(tabBody, data);
    else if (activeCultureTab === "intel_feed") renderIntelFeedTab(tabBody, data);
  }

  // TAB 1: RELIGIOUS ORDERS & ROMAN SEATS
  function renderOrdersTab(tabBody, data) {
    var orders = data.orders || [];

    var introCard = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 8px 0;color:var(--accent-gold);font-size:16px;" }, "🏛️ The Great Religious Orders & Their Roman Intellectual Strongholds"),
      el("p", { style: "margin:0;font-size:12px;color:var(--text-muted);line-height:1.5;" },
        "In Rome, religious orders are not merely spiritual communities; they operate the Pontifical Universities, " +
        "draft theological dossiers for the Dicasteries, staff the Vatican astronomical observatory, conduct critical biblical and " +
        "hagiographical archaeology, and provide consultors to the Dicastery for the Doctrine of the Faith (DDF)."
      )
    ]);
    tabBody.appendChild(introCard);

    var grid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(380px, 1fr));gap:16px;" });
    orders.forEach(function (ord) {
      var card = el("div", { style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:16px;display:flex;flex-direction:column;justify-content:space-between;" }, null, [
        el("div", null, null, [
          el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;" }, null, [
            el("h4", { style: "margin:0;color:var(--accent-gold);font-size:16px;" }, ord.name + " (" + ord.acronym + ")"),
            el("span", { style: BADGE_CSS + "font-size:10px;margin:0;" }, ord.founder ? ord.founder.split("(")[0].trim() : "Religious Order")
          ]),
          el("div", { style: "font-size:11px;font-style:italic;color:var(--accent-cyan);margin-bottom:8px;" }, "Motto: " + ord.motto),
          el("div", { style: "font-size:12px;color:var(--text-main);margin-bottom:8px;line-height:1.4;" }, [
            el("strong", { style: "color:var(--on-accent);" }, "📍 Roman Seat: "),
            ord.roman_seat
          ]),
          el("div", { style: "font-size:12px;color:var(--text-muted);margin-bottom:10px;line-height:1.45;" }, [
            el("strong", { style: "color:var(--on-accent);" }, "Charism: "),
            ord.charism
          ]),
          el("div", { style: "background:rgba(0,0,0,0.25);border-left:3px solid var(--accent-gold);padding:8px 10px;border-radius:0 4px 4px 0;margin-bottom:12px;font-size:11px;line-height:1.4;color:var(--text-main);" }, [
            el("strong", { style: "color:var(--accent-gold);" }, "Curial Office & Role: "),
            ord.curial_role
          ]),

          // Pontifical Houses
          el("div", { style: "margin-bottom:12px;" }, null, [
            el("strong", { style: "font-size:12px;color:var(--accent-cyan);display:block;margin-bottom:6px;" }, "Pontifical Academic Faculties & Centers:"),
            el("div", { style: "display:flex;flex-direction:column;gap:6px;" }, null,
              (ord.pontifical_academic_houses || []).map(function (h) {
                return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:4px;padding:8px;" }, null, [
                  el("div", { style: "font-weight:600;font-size:12px;color:var(--on-accent);" }, h.name),
                  el("div", { style: "font-size:11px;color:var(--accent-gold);margin-top:2px;" }, "Founded: " + h.founded),
                  el("div", { style: "font-size:11px;color:var(--text-muted);margin-top:2px;" }, h.influence)
                ]);
              })
            )
          ]),

          // Premier Journals
          el("div", { style: "margin-bottom:12px;" }, null, [
            el("strong", { style: "font-size:11px;color:var(--text-muted);display:block;margin-bottom:4px;" }, "Flagship Journals:"),
            el("div", { style: "display:flex;gap:4px;flex-wrap:wrap;" }, null,
              (ord.premier_journals || []).map(function (j) {
                return el("span", { style: BADGE_CSS + "border-color:var(--border);color:var(--text-main);font-size:10px;margin-bottom:4px;" }, j);
              })
            )
          ])
        ]),

        // Intellectual Vectors
        el("div", { style: "border-top:1px solid var(--border);padding-top:10px;font-size:11px;color:var(--text-muted);" }, null, [
          el("strong", { style: "color:var(--accent-cyan);display:block;margin-bottom:4px;" }, "Current Curial Intellectual Vectors:"),
          el("ul", { style: "margin:0;padding-left:16px;" }, null,
            (ord.curial_intellectual_vectors || []).map(function (v) {
              return el("li", { style: "margin-bottom:2px;" }, v);
            })
          )
        ])
      ]);
      grid.appendChild(card);
    });
    tabBody.appendChild(grid);
  }

  // TAB 2: SCHOLARLY JOURNALS & VATICAN GAZETTES
  function renderJournalsTab(tabBody, data) {
    var journals = data.journals || [];

    var filterCard = el("div", { style: CARD_CSS }, null, [
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px;" }, null, [
        el("div", null, null, [
          el("h3", { style: "margin:0 0 4px 0;color:var(--accent-gold);font-size:16px;" }, "📚 Peer-Reviewed Journals & Holy See Periodicals"),
          el("p", { style: "margin:0;font-size:12px;color:var(--text-muted);" }, "The premier speculative, patristic, hagiographical, and canonical publications shaping Catholic doctrine.")
        ]),
        el("div", { style: "display:flex;gap:6px;flex-wrap:wrap;" }, null, [
          createJournalFilterBtn("all", "All Journals (" + journals.length + ")"),
          createJournalFilterBtn("jesuit", "Jesuits"),
          createJournalFilterBtn("dominican", "Dominicans"),
          createJournalFilterBtn("benedictine", "Benedictines"),
          createJournalFilterBtn("bollandist", "Bollandists"),
          createJournalFilterBtn("official", "Holy See Official")
        ])
      ])
    ]);
    tabBody.appendChild(filterCard);

    var grid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(360px, 1fr));gap:14px;" });
    
    var filtered = journals.filter(function (j) {
      if (journalFilter === "all") return true;
      var str = (j.id + " " + j.publisher + " " + j.title).toLowerCase();
      if (journalFilter === "jesuit") return str.includes("jesuit") || str.includes("civilt") || str.includes("theological");
      if (journalFilter === "dominican") return str.includes("dominic") || str.includes("thomiste") || str.includes("angelicum") || str.includes("nova");
      if (journalFilter === "benedictine") return str.includes("benedict") || str.includes("anselm");
      if (journalFilter === "bollandist") return str.includes("bolland");
      if (journalFilter === "official") return str.includes("holy see") || str.includes("dicastery") || str.includes("acta") || str.includes("osservatore") || str.includes("notitiae") || str.includes("communicationes");
      return true;
    });

    filtered.forEach(function (j) {
      var card = el("div", { style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:14px;display:flex;flex-direction:column;justify-content:space-between;" }, null, [
        el("div", null, null, [
          el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
            el("h4", { style: "margin:0;color:var(--accent-cyan);font-size:15px;" }, j.title),
            el("span", { style: BADGE_CSS + "font-size:9px;margin:0;" }, j.frequency)
          ]),
          el("div", { style: "font-size:11px;color:var(--accent-gold);margin-bottom:6px;" }, j.publisher + " · Founded " + j.founded),
          el("div", { style: "font-size:11px;color:var(--text-muted);margin-bottom:8px;" }, "Languages: " + j.languages + " | Location: " + j.headquarters),
          el("div", { style: "font-size:12px;color:var(--text-main);line-height:1.45;margin-bottom:10px;background:rgba(0,0,0,0.2);padding:8px;border-radius:4px;" }, [
            el("strong", { style: "color:var(--on-accent);display:block;margin-bottom:2px;" }, "Curial Authority & Status:"),
            j.curial_status
          ]),
          el("div", { style: "font-size:11px;color:var(--text-muted);line-height:1.4;margin-bottom:10px;" }, [
            el("strong", { style: "color:var(--accent-gold);" }, "2026 Intellectual Focus: "),
            j.current_focus_2026
          ])
        ]),
        el("a", {
          href: j.url,
          target: "_blank",
          rel: "noopener noreferrer",
          style: BTN_CSS + "display:block;text-align:center;text-decoration:none;font-weight:700;color:var(--accent-cyan);border-color:var(--accent-cyan);margin-top:6px;"
        }, "Visit Journal Archive ↗")
      ]);
      grid.appendChild(card);
    });

    tabBody.appendChild(grid);

    function createJournalFilterBtn(key, label) {
      return el("button", {
        style: journalFilter === key ? BTN_ACTIVE : BTN_CSS,
        onclick: function () {
          journalFilter = key;
          renderJournalsTab(tabBody, data);
        }
      }, label);
    }
  }

  // TAB 3: CURIAL BOOKSHELF & THEOLOGICAL DEBATES
  function renderBookshelfTab(tabBody, data) {
    var debates = data.curial_debates || [];
    var books = data.curial_bookshelf || [];

    // Part 1: Top 5 Active Curial Debates
    var debatesCard = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 6px 0;color:var(--accent-gold);font-size:16px;" }, "🔥 High-Priority Doctrinal Debates & Curial Fault Lines (2025–2026)"),
      el("p", { style: "margin:0 0 14px 0;font-size:12px;color:var(--text-muted);" }, 
        "The core philosophical and dogmatic questions occupying Cardinal prefects, university rectorates, and DDF consultors in Rome today."
      ),
      el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(360px, 1fr));gap:12px;" }, null,
        debates.map(function (d) {
          return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-left:3px solid var(--accent-gold);border-radius:0 6px 6px 0;padding:12px 14px;" }, null, [
            el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;" }, null, [
              el("strong", { style: "color:var(--on-accent);font-size:13px;" }, d.title),
              el("span", { style: BADGE_CSS + "font-size:9px;margin:0;" }, d.curial_status ? d.curial_status.split("—")[0].trim() : "Active")
            ]),
            el("div", { style: "font-size:11px;color:var(--accent-cyan);margin-bottom:6px;" }, "Dicasteries: " + (d.dicasteries_involved || []).join(", ")),
            el("div", { style: "font-size:12px;color:var(--text-muted);line-height:1.45;margin-bottom:8px;" }, d.core_thesis),
            el("div", { style: "font-size:11px;color:var(--text-main);" }, [
              el("strong", { style: "color:var(--accent-gold);" }, "Key Thinkers Cited: "),
              (d.key_thinkers || []).join(", ")
            ])
          ]);
        })
      )
    ]);
    tabBody.appendChild(debatesCard);

    // Part 2: The Curial Bookshelf
    var booksCard = el("div", { style: CARD_CSS }, null, [
      el("h3", { style: "margin:0 0 6px 0;color:var(--accent-cyan);font-size:16px;" }, "📚 The Curial Bookshelf: What the Magisterium is Reading"),
      el("p", { style: "margin:0 0 14px 0;font-size:12px;color:var(--text-muted);" },
        "The seminal philosophical monographs, patristic ressourcement volumes, and systematic treaties found on the desks of Vatican prelates."
      ),
      el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(340px, 1fr));gap:12px;" }, null,
        books.map(function (b) {
          return el("div", { style: "background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:12px;" }, null, [
            el("div", { style: "font-weight:700;color:var(--accent-gold);font-size:14px;margin-bottom:2px;" }, b.title),
            el("div", { style: "font-size:11px;color:var(--text-muted);margin-bottom:6px;" }, "Author: " + b.author + " (" + b.original_year + ")"),
            el("div", { style: "font-size:12px;color:var(--text-main);line-height:1.4;margin-bottom:8px;" }, b.why_read_now),
            el("div", { style: "background:rgba(0,0,0,0.2);padding:6px 8px;border-radius:4px;font-size:11px;display:flex;justify-content:space-between;align-items:center;" }, null, [
              el("span", { style: "color:var(--accent-cyan);" }, "Core Concept: " + b.key_concept),
              el("span", { style: "color:var(--text-muted);font-size:10px;" }, (b.dicasteries_reading || []).join(" / "))
            ])
          ]);
        })
      )
    ]);
    tabBody.appendChild(booksCard);
  }

  // TAB 4: LIVE CURIAL NEWS & INTEL FEED
  function renderIntelFeedTab(tabBody, data) {
    var news = data.curial_news_feed || [];

    var headerCard = el("div", { style: CARD_CSS }, null, [
      el("div", { style: "display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;" }, null, [
        el("div", null, null, [
          el("h3", { style: "margin:0 0 4px 0;color:var(--accent-gold);font-size:16px;" }, "📰 Live Curial Dispatches, Editorials & Analysis"),
          el("p", { style: "margin:0;font-size:12px;color:var(--text-muted);" }, "Aggregated intelligence from L'Osservatore Romano, Civiltà Cattolica, Revue Thomiste, and Rome correspondents.")
        ]),
        el("span", { style: BADGE_CSS + "border-color:var(--ok);color:var(--ok);" }, "Verified Dispatches")
      ])
    ]);
    tabBody.appendChild(headerCard);

    var feedGrid = el("div", { style: "display:grid;grid-template-columns:repeat(auto-fit, minmax(360px, 1fr));gap:12px;" });
    news.forEach(function (n) {
      var card = el("div", { style: "background:var(--bg-panel);border:1px solid var(--border);border-radius:6px;padding:14px;display:flex;flex-direction:column;justify-content:space-between;" }, null, [
        el("div", null, null, [
          el("div", { style: "display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;" }, null, [
            el("span", { style: BADGE_CSS + "font-size:9px;" }, n.source),
            el("span", { style: "font-size:11px;color:var(--text-muted);" }, n.date)
          ]),
          el("h4", { style: "margin:0 0 6px 0;color:var(--on-accent);font-size:14px;line-height:1.35;" }, n.title),
          el("div", { style: "font-size:11px;color:var(--accent-cyan);margin-bottom:8px;font-weight:600;" }, n.category + " · #" + n.tag),
          el("p", { style: "margin:0 0 10px 0;font-size:12px;color:var(--text-muted);line-height:1.45;" }, n.summary)
        ]),
        el("a", {
          href: n.url,
          target: "_blank",
          rel: "noopener noreferrer",
          style: BTN_CSS + "display:block;text-align:center;text-decoration:none;font-weight:600;padding:4px 8px;font-size:11px;color:var(--accent-gold);border-color:var(--accent-gold);"
        }, "Read Full Dispatch ↗")
      ]);
      feedGrid.appendChild(card);
    });
    tabBody.appendChild(feedGrid);
  }

  window.JarvisModules["vatican_culture"] = { load: load };
})();
