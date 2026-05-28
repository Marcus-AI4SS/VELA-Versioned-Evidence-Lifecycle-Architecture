const fs = require("fs");
const path = require("path");

const DEFAULT_BOARD_FRAGMENT = "/board/69e5d2da0000000016025f45";
const DEFAULT_OUTFILE = path.join(process.cwd(), "outputs", "xiaohongshu_ai_board.json");
const DEFAULT_MAX_NOTES = 24;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureParentDir(filePath) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
}

function parseArgs(argv) {
  return {
    boardFragment: argv[2] || DEFAULT_BOARD_FRAGMENT,
    outputFile: argv[3] || DEFAULT_OUTFILE,
    maxNotes: Number(argv[4] || DEFAULT_MAX_NOTES),
  };
}

function readBrowserWsUrl() {
  const devtoolsPortFile = path.join(
    process.env.LOCALAPPDATA || "<USER_HOME>\\AppData\\Local",
    "Google",
    "Chrome",
    "User Data",
    "DevToolsActivePort",
  );
  const lines = fs.readFileSync(devtoolsPortFile, "utf8").trim().split(/\r?\n/);
  if (lines.length < 2) {
    throw new Error(`Invalid DevToolsActivePort file: ${devtoolsPortFile}`);
  }
  return `ws://127.0.0.1:${lines[0]}${lines[1]}`;
}

class CDPClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.nextId = 1;
    this.pending = new Map();
    this.ws = null;
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) {
          reject(new Error(JSON.stringify(message.error)));
        } else {
          resolve(message);
        }
      }
    };
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
  }

  async close() {
    if (!this.ws) {
      return;
    }
    await new Promise((resolve) => {
      this.ws.onclose = resolve;
      this.ws.close();
    });
  }

  send(method, params = {}, sessionId) {
    return new Promise((resolve, reject) => {
      const id = this.nextId++;
      this.pending.set(id, { resolve, reject });
      const payload = { id, method, params };
      if (sessionId) {
        payload.sessionId = sessionId;
      }
      this.ws.send(JSON.stringify(payload));
    });
  }
}

function parseJsonResult(rawMessage) {
  const value = rawMessage?.result?.result?.value;
  if (typeof value !== "string") {
    throw new Error(`Expected string result from Runtime.evaluate, got: ${JSON.stringify(rawMessage)}`);
  }
  return JSON.parse(value);
}

async function attachToTarget(client, targetId) {
  const response = await client.send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  return response.result.sessionId;
}

async function createWorkerTarget(client) {
  const created = await client.send("Target.createTarget", {
    url: "about:blank",
    newWindow: false,
    background: true,
  });
  const targetId = created.result.targetId;
  const sessionId = await attachToTarget(client, targetId);
  await client.send("Page.enable", {}, sessionId);
  await client.send("Runtime.enable", {}, sessionId);
  return { targetId, sessionId };
}

async function findBoardTarget(client, boardFragment) {
  const response = await client.send("Target.getTargets");
  const boardTarget = response.result.targetInfos.find(
    (target) => target.type === "page" && target.url.includes(boardFragment),
  );
  if (!boardTarget) {
    throw new Error(`Board tab not found for fragment: ${boardFragment}`);
  }
  return boardTarget;
}

async function evaluateJson(client, sessionId, expression, awaitPromise = false) {
  const response = await client.send(
    "Runtime.evaluate",
    {
      expression,
      awaitPromise,
      returnByValue: true,
    },
    sessionId,
  );
  return parseJsonResult(response);
}

function buildBoardExtractionExpression() {
  return String.raw`(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const clean = (value) => (value || "").replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
    const toInt = (text) => {
      const normalized = clean(text).replace(/,/g, "");
      const wanMatch = normalized.match(/([\d.]+)w/i);
      if (wanMatch) {
        return Math.round(Number(wanMatch[1]) * 10000);
      }
      const digits = normalized.replace(/[^\d]/g, "");
      return digits ? Number(digits) : 0;
    };

    const cards = new Map();
    const collect = () => {
      const sections = [...document.querySelectorAll("section.note-item")];
      sections.forEach((section, idx) => {
        const link = section.querySelector('a.cover[href*="/board/"], a.title[href*="/board/"]');
        const explore = section.querySelector('a[href*="/explore/"]');
        const href = link ? new URL(link.getAttribute("href"), location.origin).href : "";
        const exploreHref = explore ? new URL(explore.getAttribute("href"), location.origin).href : "";
        const noteIdMatch =
          href.match(/\/board\/[^/]+\/([a-zA-Z0-9]+)(?:\?|$)/) ||
          exploreHref.match(/\/explore\/([a-zA-Z0-9]+)(?:\?|$)/);
        const noteId = noteIdMatch ? noteIdMatch[1] : "";
        if (!noteId || !href) {
          return;
        }
        cards.set(noteId, {
          index: Number(section.dataset.index || idx),
          noteId,
          href,
          exploreHref,
          title: clean(section.querySelector("a.title span, a.title")?.textContent),
          author: clean(section.querySelector(".author .name")?.textContent),
          likedCount: toInt(section.querySelector(".like-wrapper .count")?.textContent),
        });
      });
    };

    collect();
    let previousSize = cards.size;
    let stableRounds = 0;
    for (let i = 0; i < 40; i += 1) {
      window.scrollTo(0, document.body.scrollHeight);
      await sleep(800);
      collect();
      if (cards.size === previousSize) {
        stableRounds += 1;
      } else {
        stableRounds = 0;
      }
      previousSize = cards.size;
      if (stableRounds >= 4) {
        break;
      }
    }
    window.scrollTo(0, 0);

    const body = document.body ? document.body.innerText : "";
    const lines = body.split(/\n/).map(clean).filter(Boolean);
    const boardTitle = clean(document.title.replace(/\s*-\s*小红书\s*$/, ""));
    const titleIndex = lines.findIndex((line) => line === boardTitle);
    let owner = "";
    if (titleIndex >= 0) {
      owner =
        lines
          .slice(titleIndex + 1, titleIndex + 6)
          .find(
            (line) =>
              line &&
              line !== "暂无简介" &&
              !line.startsWith("笔记") &&
              !line.startsWith("粉丝") &&
              line !== "编辑专辑",
          ) || "";
    }
    const totalMatch = body.match(/笔记[・·]\s*(\d+)/) || body.match(/共\s*(\d+)\s*篇笔记/);

    return JSON.stringify({
      boardTitle,
      owner,
      totalNotes: totalMatch ? Number(totalMatch[1]) : null,
      cards: [...cards.values()].sort((left, right) => left.index - right.index),
    });
  })()`;
}

function buildNoteExtractionExpression() {
  return String.raw`(async () => {
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const clean = (value) =>
      (value || "")
        .replace(/\u00a0/g, " ")
        .replace(/[ \t]+\n/g, "\n")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
    const toInt = (text) => {
      const normalized = clean(text).replace(/,/g, "");
      const wanMatch = normalized.match(/([\d.]+)w/i);
      if (wanMatch) {
        return Math.round(Number(wanMatch[1]) * 10000);
      }
      const digits = normalized.replace(/[^\d]/g, "");
      return digits ? Number(digits) : 0;
    };

    for (let i = 0; i < 5; i += 1) {
      window.scrollTo(0, document.body.scrollHeight);
      await sleep(1100);
    }

    const title = clean(document.title.replace(/\s*-\s*小红书\s*$/, ""));
    const bodyText = clean(document.body ? document.body.innerText : "");
    const lines = bodyText.split(/\n/).map(clean).filter(Boolean);
    const titleIndex = lines.findIndex((line) => line === title);

    let author = "";
    if (titleIndex > 0) {
      for (let i = titleIndex - 1; i >= Math.max(0, titleIndex - 4); i -= 1) {
        const candidate = lines[i];
        if (
          candidate &&
          candidate !== "关注" &&
          candidate !== title &&
          !candidate.includes("ICP备") &&
          !["创作中心", "业务合作", "发现", "直播", "发布", "通知", "我", "更多"].includes(candidate)
        ) {
          author = candidate;
          break;
        }
      }
    }
    if (!author) {
      author = clean(
        document.querySelector('a[href*="/user/profile/"] .name, a.name, .author .name')?.textContent,
      );
    }

    const tagLines = [...new Set(lines.filter((line) => line.startsWith("#")))];
    const timeLine =
      lines.find((line) => /^\d{2}-\d{2}\s*\S*$/.test(line)) ||
      lines.find((line) => /^\d{1,2}天前\s*\S*$/.test(line)) ||
      "";

    let body = "";
    if (titleIndex >= 0) {
      const tail = lines.slice(titleIndex + 1);
      const stopIndex = tail.findIndex(
        (line) => /^#/.test(line) || /^\d{2}-\d{2}\s*\S*$/.test(line) || /^共\s*\d+\s*条评论$/.test(line),
      );
      body = clean((stopIndex >= 0 ? tail.slice(0, stopIndex) : tail.slice(0, 80)).join("\n"));
    }

    const topLevelComments = [...document.querySelectorAll('[id^="comment-"]')]
      .filter((element) => !element.parentElement?.closest('[id^="comment-"]'))
      .map((element) => {
        const counts = [...element.querySelectorAll(".interactions .count")].map((node) => toInt(node.textContent));
        return {
          commentId: element.id,
          author: clean(element.querySelector("a.name, .author .name")?.textContent),
          content: clean(
            element.querySelector(".content .note-text")?.textContent || element.querySelector(".content")?.textContent,
          ),
          dateText: clean(element.querySelector(".date")?.innerText),
          likeCount: counts[0] || 0,
          replyCount: counts[1] || 0,
        };
      })
      .filter((comment) => comment.author && comment.content);

    const totalCommentMatch = bodyText.match(/共\s*(\d+)\s*条评论/);

    return JSON.stringify({
      title,
      author,
      body,
      tags: tagLines,
      timeLine,
      totalCommentsVisibleText: totalCommentMatch ? Number(totalCommentMatch[1]) : null,
      visibleTopLevelComments: topLevelComments,
      rawBodyText: bodyText,
    });
  })()`;
}

function buildCommentRanking(notes) {
  return notes
    .flatMap((note) =>
      (note.visibleTopLevelComments || []).map((comment) => ({
        noteId: note.noteId,
        noteTitle: note.pageTitle || note.cardTitle,
        noteUrl: note.boardUrl,
        ...comment,
      })),
    )
    .sort((left, right) => right.likeCount - left.likeCount)
    .slice(0, 20);
}

async function main() {
  const args = parseArgs(process.argv);
  const client = new CDPClient(readBrowserWsUrl());
  await client.connect();

  try {
    const boardTarget = await findBoardTarget(client, args.boardFragment);
    const boardSessionId = await attachToTarget(client, boardTarget.targetId);
    console.log(`Found board tab: ${boardTarget.title}`);
    const board = await evaluateJson(client, boardSessionId, buildBoardExtractionExpression(), true);
    const selectedCards = board.cards.slice(0, args.maxNotes);
    console.log(`Collected ${selectedCards.length} board cards from ${board.boardTitle}`);

    const worker = await createWorkerTarget(client);
    const notes = [];
    for (const card of selectedCards) {
      console.log(`Reading note ${card.index + 1}/${selectedCards.length}: ${card.title}`);
      await client.send("Page.navigate", { url: card.href }, worker.sessionId);
      await sleep(6500);
      const note = await evaluateJson(client, worker.sessionId, buildNoteExtractionExpression(), true);
      notes.push({
        index: card.index + 1,
        noteId: card.noteId,
        boardUrl: card.href,
        exploreUrl: card.exploreHref,
        cardTitle: card.title,
        cardAuthor: card.author,
        cardLikedCount: card.likedCount,
        pageTitle: note.title,
        pageAuthor: note.author,
        body: note.body,
        tags: note.tags,
        timeLine: note.timeLine,
        totalCommentsVisibleText: note.totalCommentsVisibleText,
        visibleTopLevelComments: note.visibleTopLevelComments,
        rawBodyText: note.rawBodyText,
      });
    }
    await client.send("Target.closeTarget", { targetId: worker.targetId });

    const payload = {
      extractedAt: new Date().toISOString(),
      board: {
        title: board.boardTitle,
        owner: board.owner,
        totalNotes: board.totalNotes,
        url: boardTarget.url,
      },
      notes,
      topCommentsByLikes: buildCommentRanking(notes),
    };

    ensureParentDir(args.outputFile);
    fs.writeFileSync(args.outputFile, JSON.stringify(payload, null, 2), "utf8");
    console.log(`Saved ${notes.length} notes to ${args.outputFile}`);
  } finally {
    await client.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
