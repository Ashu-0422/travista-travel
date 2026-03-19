(function () {
  const rootNode = document.getElementById("chatApp");
  if (!rootNode || !window.React || !window.ReactDOM) {
    return;
  }

  const tripId = rootNode.dataset.tripId;
  const tripName = rootNode.dataset.tripName || "Trip Chat";
  const backUrl = rootNode.dataset.backUrl || "/home";
  const apiUrl = `/chat/${tripId}/messages`;
  const feedbackUrl = `/chat/${tripId}/feedback`;
  const initialChatClosed = rootNode.dataset.chatClosed === "true";
  const initialFeedbackSaved = rootNode.dataset.feedbackSaved === "true";

  const e = React.createElement;
  const useState = React.useState;
  const useEffect = React.useEffect;
  const useMemo = React.useMemo;
  const useRef = React.useRef;

  function MessageBubble(props) {
    const msg = props.msg;
    return e(
      "article",
      { className: `bubble ${msg.sender_role === "system" ? "system" : msg.is_mine ? "mine" : "their"}` },
      e("p", { className: "message-text" }, msg.message_text),
      e(
        "div",
        { className: "message-meta" },
        e(
          "span",
          { className: "sender" },
          msg.sender_role === "system" ? "Travista" : msg.is_mine ? "You" : msg.sender_name || msg.username
        ),
        e("span", { className: "time" }, msg.created_at || "")
      )
    );
  }

  function App() {
    const [messages, setMessages] = useState([]);
    const [operator, setOperator] = useState({ name: "", email: "", phone: "" });
    const [text, setText] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(true);
    const [chatClosed, setChatClosed] = useState(initialChatClosed);
    const [feedbackSaved, setFeedbackSaved] = useState(initialFeedbackSaved);
    const [feedbackText, setFeedbackText] = useState("");
    const [savingFeedback, setSavingFeedback] = useState(false);
    const listRef = useRef(null);

    const participantCount = useMemo(function () {
      const people = new Set();
      for (const msg of messages) {
        if (msg.username) {
          people.add(msg.username);
        }
      }
      return people.size;
    }, [messages]);

    function scrollToBottom() {
      if (!listRef.current) {
        return;
      }
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }

    async function loadMessages(showLoader) {
      if (showLoader) {
        setLoading(true);
      }

      try {
        const response = await fetch(apiUrl, {
          headers: { "Accept": "application/json" },
          credentials: "same-origin",
        });
        if (!response.ok) {
          setError("Unable to load chat right now.");
          return;
        }

        const data = await response.json();
        setMessages(Array.isArray(data.messages) ? data.messages : []);
        setOperator(data.operator || { name: "", email: "", phone: "" });
        setChatClosed(Boolean(data.chat_closed));
        setFeedbackSaved(Boolean(data.feedback));
        setError("");
      } catch (err) {
        setError("Network error while loading messages.");
      } finally {
        setLoading(false);
      }
    }

    async function sendMessage(evt) {
      evt.preventDefault();
      const cleanText = text.trim();
      if (!cleanText || sending) {
        return;
      }

      setSending(true);
      try {
        const response = await fetch(apiUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          body: JSON.stringify({ message: cleanText }),
        });

        if (!response.ok) {
          if (response.status === 403) {
            setChatClosed(true);
            setError("Trip completed. Chat is disabled now. Please share your feedback.");
            return;
          }
          setError("Message not sent. Try again.");
          return;
        }

        const data = await response.json();
        setMessages(Array.isArray(data.messages) ? data.messages : []);
        setText("");
        setError("");
      } catch (err) {
        setError("Network error while sending message.");
      } finally {
        setSending(false);
      }
    }

    async function submitFeedback(evt) {
      evt.preventDefault();
      const cleanFeedback = feedbackText.trim();
      if (!cleanFeedback || savingFeedback) {
        return;
      }

      setSavingFeedback(true);
      try {
        const response = await fetch(feedbackUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
          },
          body: JSON.stringify({ feedback: cleanFeedback }),
        });

        if (!response.ok) {
          setError("Unable to save feedback right now.");
          return;
        }

        setFeedbackSaved(true);
        setFeedbackText("");
        setError("");
      } catch (err) {
        setError("Network error while saving feedback.");
      } finally {
        setSavingFeedback(false);
      }
    }

    useEffect(function () {
      loadMessages(true);
      const poll = setInterval(function () {
        loadMessages(false);
      }, 4000);
      return function () {
        clearInterval(poll);
      };
    }, []);

    useEffect(function () {
      scrollToBottom();
    }, [messages.length]);

    return e(
      "div",
      { className: "chat-page" },
      e(
        "header",
        { className: "topbar" },
        e(
          "div",
          null,
          e("h1", null, tripName),
          e(
            "p",
            null,
            `Trip group chat for booked passengers`,
            participantCount > 0 ? ` | ${participantCount} participant(s)` : ""
          )
        ),
        e(
          "div",
          { className: "topbar-actions" },
          operator.phone
            ? e(
                "a",
                { className: "call-btn", href: `tel:${operator.phone}` },
                `Call Operator ${operator.phone}`
              )
            : null,
          e("a", { className: "back-btn", href: backUrl }, "Back to Booking")
        )
      ),
      e(
        "main",
        { className: "chat-shell" },
        e(
          "section",
          { className: "operator-card" },
          e("h2", null, "Operator Contact"),
          e("p", null, operator.name || "-"),
          e("p", null, operator.email || "-"),
          e("p", null, operator.phone || "-")
        ),
        e(
          "section",
          { className: "chat-panel" },
          error ? e("p", { className: "error" }, error) : null,
          loading
            ? e("p", { className: "empty" }, "Loading messages...")
            : null,
          !loading && messages.length === 0
            ? e("p", { className: "empty" }, "No messages yet. Start the trip chat.")
            : null,
          chatClosed
            ? e(
                "div",
                { className: "chat-closed-banner" },
                e("strong", null, "Trip completed."),
                e("span", null, " Chat is disabled now. Please share your feedback.")
              )
            : null,
          e(
            "div",
            { className: "messages", ref: listRef },
            messages.map(function (msg) {
              return e(MessageBubble, { msg: msg, key: msg.id || `${msg.username}-${msg.created_at}` });
            })
          ),
          chatClosed
            ? feedbackSaved
              ? e("div", { className: "feedback-thanks" }, "Thank you for your feedback.")
              : e(
                  "form",
                  { className: "feedback-form", onSubmit: submitFeedback },
                  e("textarea", {
                    value: feedbackText,
                    onChange: function (evt) {
                      setFeedbackText(evt.target.value);
                    },
                    rows: 3,
                    placeholder: "Share your trip feedback...",
                    required: true,
                    maxLength: 1000,
                  }),
                  e(
                    "button",
                    { type: "submit", disabled: savingFeedback || !feedbackText.trim() },
                    savingFeedback ? "Saving..." : "Submit Feedback"
                  )
                )
            : e(
                "form",
                { className: "composer", onSubmit: sendMessage },
                e("textarea", {
                  value: text,
                  onChange: function (evt) {
                    setText(evt.target.value);
                  },
                  rows: 2,
                  placeholder: "Message other passengers...",
                  required: true,
                  maxLength: 1000,
                }),
                e(
                  "button",
                  { type: "submit", disabled: sending || !text.trim() },
                  sending ? "Sending..." : "Send"
                )
              )
        )
      )
    );
  }

  const root = ReactDOM.createRoot(rootNode);
  root.render(e(App));
})();
