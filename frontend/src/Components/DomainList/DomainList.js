import React, { useEffect, useState } from "react";
import DomainCard from "../DomainCard/DomainCard";
import "./DomainList.css";
import { useNavigate } from "react-router-dom";

const DomainList = () => {
  const [domainNames, setDomainNames] = useState([]);
  const [domainDescriptions, setDomainDescriptions] = useState({});
  const [visibleDomains, setVisibleDomains] = useState(6);
  const [loading, setLoading] = useState(true);
  const [loadingDescriptions, setLoadingDescriptions] = useState({});
  const [searchInput, setSearchInput] = useState("");
  const [feedbackRating, setFeedbackRating] = useState(1);
  const [feedbackName, setFeedbackName] = useState("");
  const [feedbackEmail, setFeedbackEmail] = useState("");
  const [feedbackComment, setFeedbackComment] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const navigate = useNavigate();

  const handleLoadMore = () => {
    const currentVisible = visibleDomains;
    const newVisible = Math.min(currentVisible + 6, domainNames.length);
    setVisibleDomains(newVisible);
    
    // Generate descriptions for newly visible domains that don't have descriptions yet
    const newlyVisibleDomains = domainNames.slice(currentVisible, newVisible);
    const domainsNeedingDescriptions = newlyVisibleDomains.filter(
      domain => !domainDescriptions[domain] && !loadingDescriptions[domain]
    );
    
    if (domainsNeedingDescriptions.length > 0) {
      fetchBulkDescriptions(domainsNeedingDescriptions);
    }
  };

  const handleNewSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim() === "") return;
    
    sessionStorage.setItem("userPrompt", searchInput);
    sessionStorage.removeItem("cachedDomains");
    sessionStorage.removeItem("cachedDescriptions");
    setLoading(true);
    setDomainDescriptions({});
    setLoadingDescriptions({});
    setVisibleDomains(6);
    fetchDomains(searchInput);
  };

  const fetchDomains = async (prompt) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/generate-domains/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      const data = await response.json();
      setDomainNames(data.domains);
      
      // Cache the results
      sessionStorage.setItem("cachedDomains", JSON.stringify({
        prompt,
        domains: data.domains,
        timestamp: Date.now()
      }));
      
      setLoading(false);
      
      // Immediately fetch descriptions for first 6 domains
      const firstSixDomains = data.domains.slice(0, 6);
      if (firstSixDomains.length > 0) {
        fetchBulkDescriptions(firstSixDomains);
      }
      
    } catch (error) {
      console.error("Error fetching domains:", error);
      setLoading(false);
    }
  };

  const fetchBulkDescriptions = async (domainList) => {
    const prompt = sessionStorage.getItem("userPrompt") || "default";
    
    // Set loading state for these domains
    const newLoadingState = {};
    domainList.forEach(domain => {
      newLoadingState[domain] = true;
    });
    setLoadingDescriptions(prev => ({ ...prev, ...newLoadingState }));

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/generate-bulk-descriptions/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          prompt, 
          domain_names: domainList 
        }),
      });

      const data = await response.json();
      
      // Update descriptions state
      setDomainDescriptions(prev => ({ 
        ...prev, 
        ...data.descriptions 
      }));
      
      // Clear loading state for these domains
      setLoadingDescriptions(prev => {
        const newState = { ...prev };
        domainList.forEach(domain => {
          delete newState[domain];
        });
        return newState;
      });
      
      // Cache descriptions
      const existingCache = JSON.parse(sessionStorage.getItem("cachedDescriptions") || "{}");
      const updatedCache = { ...existingCache, ...data.descriptions };
      sessionStorage.setItem("cachedDescriptions", JSON.stringify(updatedCache));
      
    } catch (error) {
      console.error("Error fetching bulk descriptions:", error);
      
      // Clear loading state on error
      setLoadingDescriptions(prev => {
        const newState = { ...prev };
        domainList.forEach(domain => {
          delete newState[domain];
        });
        return newState;
      });
    }
  };

  useEffect(() => {
    const prompt = sessionStorage.getItem("userPrompt") || "default";
    setSearchInput(prompt);

    // Check for cached domains
    const cachedData = sessionStorage.getItem("cachedDomains");
    if (cachedData) {
      const { prompt: cachedPrompt, domains } = JSON.parse(cachedData);
      if (cachedPrompt === prompt) {
        setDomainNames(domains);
        setLoading(false);
        
        // Check for cached descriptions
        const cachedDescriptions = JSON.parse(sessionStorage.getItem("cachedDescriptions") || "{}");
        setDomainDescriptions(cachedDescriptions);
        
        // If we have domains but no descriptions for first 6, fetch them
        const firstSixDomains = domains.slice(0, 6);
        const domainsNeedingDescriptions = firstSixDomains.filter(
          domain => !cachedDescriptions[domain]
        );
        
        if (domainsNeedingDescriptions.length > 0) {
          fetchBulkDescriptions(domainsNeedingDescriptions);
        }
        
        return;
      }
    }
    
    fetchDomains(prompt);
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
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(feedbackData),
      });

      const result = await res.json();
      if (res.ok) {
        setFeedbackStatus("Feedback submitted successfully!");
        setFeedbackRating(1);
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
        <p className="loading-text">Fetching domain Names...</p>
      </div>
    );
  }

  return (
    <div className="new-container">
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
      
      <div className="container">
        <div className="row justify-content-around">
          {domainNames.slice(0, visibleDomains).map((name, index) => (
            <div className="item col-lg-6 col-md-6 col-sm-12 mb-4" key={index}>
              <DomainCard 
                domainName={name} 
                description={domainDescriptions[name]}
                isLoading={loadingDescriptions[name] || false}
              />
            </div>
          ))}
        </div>
        
        {visibleDomains < domainNames.length && (
          <div className="load text-center">
            <button className="button" onClick={handleLoadMore}>
              Load More
            </button>
          </div>
        )}
      </div>
      
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
                  fontSize: "1.5rem"
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
            <div className="alert alert-info mt-3 text-center">
              {feedbackStatus}
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default DomainList;