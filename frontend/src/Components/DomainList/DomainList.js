import React, { useEffect, useState } from "react";
import DomainCard from "../DomainCard/DomainCard";
import "./DomainList.css";
import { useNavigate } from "react-router-dom";

const DomainList = () => {
  const [domainNames, setDomainNames] = useState([]);
  const [extraDomainNames, setExtraDomainNames] = useState([]);
  const [visibleDomains, setVisibleDomains] = useState(6);
  const [loading, setLoading] = useState(true);
  const [searchInput, setSearchInput] = useState("");
  const [feedbackRating, setFeedbackRating] = useState(1);
  const [feedbackName, setFeedbackName] = useState("");
  const [feedbackEmail, setFeedbackEmail] = useState("");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [showExtra, setShowExtra] = useState(false);

  const navigate = useNavigate();

  const handleLoadMore = () => {
    setVisibleDomains((prev) => prev + 6);
  };

  const handleNewSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim() === "") return;

    sessionStorage.setItem("userPrompt", searchInput);
    sessionStorage.removeItem("cachedDomains");
    sessionStorage.removeItem("cachedExtraDomains");
    setExtraDomainNames([]);
    setShowExtra(false);
    setLoading(true);
    fetchDomains(searchInput);
    setVisibleDomains(6);
  };

  const fetchDomains = async (prompt) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/generate-domains/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();
      setDomainNames(data.domains);

      sessionStorage.setItem(
        "cachedDomains",
        JSON.stringify({
          prompt,
          domains: data.domains,
          timestamp: Date.now(),
        })
      );

      setLoading(false);
    } catch (error) {
      console.error("Error fetching domains:", error);
      setLoading(false);
    }
  };

  const fetchExtraDomains = async (prompt) => {
    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/generate-extra-domains/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const result = await res.json();
      setExtraDomainNames(result.domains);

      // Cache extra domains
      sessionStorage.setItem(
        "cachedExtraDomains",
        JSON.stringify({
          prompt,
          domains: result.domains,
          timestamp: Date.now(),
        })
      );
    } catch (err) {
      console.error("Error fetching extra domains:", err);
    }
  };

  useEffect(() => {
    const prompt = sessionStorage.getItem("userPrompt") || "default";
    setSearchInput(prompt);

    const cachedData = sessionStorage.getItem("cachedDomains");
    const cachedExtra = sessionStorage.getItem("cachedExtraDomains");

    // Load main domains from cache if available
    if (cachedData) {
      const { prompt: cachedPrompt, domains } = JSON.parse(cachedData);
      if (cachedPrompt === prompt) {
        setDomainNames(domains);
        setLoading(false);
      } else {
        fetchDomains(prompt);
      }
    } else {
      fetchDomains(prompt);
    }

    // Load extra domains from cache if available
    if (cachedExtra) {
      const { prompt: cachedPromptExtra, domains: extra } = JSON.parse(cachedExtra);
      if (cachedPromptExtra === prompt) {
        setExtraDomainNames(extra);
      } else {
        fetchExtraDomains(prompt);
      }
    } else {
      fetchExtraDomains(prompt);
    }
  }, []);

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();

    const feedbackData = {
      rating: feedbackRating,
      name: feedbackName || null,
      email: feedbackEmail.trim() === "" ? null : feedbackEmail,
      comment: feedbackComment,
    };

    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/submit-feedback/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(feedbackData),
      });

      const result = await res.json();
      if (res.ok) {
        setFeedbackStatus("Feedback submitted successfully!");
        setFeedbackRating(0);
        setFeedbackName("");
        setFeedbackEmail("");
        setFeedbackComment("");
      } else {
        setFeedbackStatus(result.message || "Submission failed");
      }
    } catch (err) {
      console.error("Feedback error:", err);
      setFeedbackStatus("Error submitting feedback.");
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p className="loading-text">Fetching domain names...</p>
      </div>
    );
  }

  return (
    <div className="new-container">
      {/* Search Box */}
      <div className="new-search">
        <form onSubmit={handleNewSearch} className="search-box">
          <input
            type="text"
            placeholder="Search for new domain names..."
            className="search-input"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit" className="search-button">
            Search
          </button>
        </form>
      </div>

      {/* Main Domains */}
      <div className="container">
        <div className="row justify-content-around">
          {domainNames.slice(0, visibleDomains).map((name, index) => (
            <div className="item col-lg-6 col-md-6 col-sm-12 mb-4" key={index}>
              <DomainCard domainName={name} />
            </div>
          ))}
        </div>

        {/* Load More Button for Main Domains */}
        {visibleDomains < domainNames.length && (
          <div className="load text-center">
            <button className="button" onClick={handleLoadMore}>
              Load More
            </button>
          </div>
        )}
      </div>

      {/* Additional Suggestions Button */}
      {extraDomainNames.length > 0 && !showExtra && visibleDomains >= domainNames.length && (
        <div className="text-center mt-4">
          <button
            className="btn btn-outline-secondary"
            onClick={() => setShowExtra(true)}
          >
            Load More Names
          </button>
        </div>
      )}

      {/* Additional Suggestions Section */}
      {showExtra && extraDomainNames.length > 0 && (
        <div className="container mt-5">
          <div className="additional-grid">
            {extraDomainNames.map((name, index) => (
              <div className="additional-item" key={`extra-${index}`}>
                <a
                  href={`https://register.domains.lk/domains-search?keywords=${name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ textDecoration: "none", color: "inherit", cursor: "pointer" }}
                >
                  {name}.lk
                </a>
              </div>
            ))}
          </div>

          <div className="text-center mt-3">
            <button
              className="btn btn-outline-danger"
              onClick={() => setShowExtra(false)}
            >
              Hide Additional Suggestions
            </button>
          </div>
        </div>
      )}

      {/* Feedback Section */}
      <div className="feedback-section mt-5 p-4 border rounded bg-light">
        <h4 className="text-center mb-3">Share Your Feedback</h4>
        <form onSubmit={handleFeedbackSubmit} className="feedback-form">
          <h6 className="rating-header">How would you rate your experience?</h6>
          <div className="mb-3 star-rating">
            {[1, 2, 3, 4, 5].map((star) => (
              <span
                key={star}
                style={{
                  cursor: "pointer",
                  color: feedbackRating >= star ? "#ffc107" : "#e4e5e9",
                  fontSize: "1.5rem",
                }}
                onClick={() => setFeedbackRating(star)}
              >
                ★
              </span>
            ))}
          </div>

          <div className="mb-2">
            <input
              type="text"
              placeholder="Your Name (optional)"
              className="form-control"
              value={feedbackName}
              onChange={(e) => setFeedbackName(e.target.value)}
            />
          </div>

          <div className="mb-2">
            <input
              type="email"
              placeholder="Your Email (optional)"
              className="form-control"
              value={feedbackEmail}
              onChange={(e) => setFeedbackEmail(e.target.value)}
            />
          </div>

          <div className="mb-3">
            <textarea
              placeholder="Your comments..."
              className="form-control"
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn btn-primary w-100">
            Submit Feedback
          </button>

          {feedbackStatus && (
            <div className="alert alert-info mt-3 text-center">{feedbackStatus}</div>
          )}
        </form>
      </div>
    </div>
  );
};

export default DomainList;
