import React, { useEffect, useState } from 'react';
import './DomainDetails.css';

const DomainDetails = () => {
  const [domainDetails, setDomainDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const prompt = sessionStorage.getItem("userPrompt");
    const domainName = sessionStorage.getItem("selectedDomain");
    
    // Check if we already have cached description from the domain card
    const cachedDescription = sessionStorage.getItem("selectedDomainDescription");
    
    if (cachedDescription) {
      try {
        const parsedDescription = JSON.parse(cachedDescription);
        setDomainDetails(parsedDescription);
        setLoading(false);
        // Clean up the cached description
        sessionStorage.removeItem("selectedDomainDescription");
        return;
      } catch (error) {
        console.error("Error parsing cached description:", error);
      }
    }

    // If no cached description, fetch it from the API
    fetch(`${process.env.REACT_APP_API_URL}/details/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ prompt, domain_name: domainName })
    })
      .then((res) => res.json())
      .then((data) => {
        setDomainDetails(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("Error fetching domain details:", error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p className="loading-text">Fetching domain insights...</p>
      </div>
    );
  }

  if (!domainDetails) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>Failed to load domain details. Please try again.</p>
      </div>
    );
  }

  return (
    <div className="domain-details">
      <div className="container">
        <div className="content-wrapper">
          <h1 className="domain-title text-center mb-4">
            {domainDetails.domainName && domainDetails.domainName.endsWith('.lk') 
              ? domainDetails.domainName 
              : `${domainDetails.domainName || 'Unknown'}.lk`}
          </h1>

          <hr className="section-divider my-4" />

          <div className="about-domain">
            <h2 className="section-heading mb-3">
              About {domainDetails.domainName && domainDetails.domainName.endsWith('.lk') 
                ? domainDetails.domainName 
                : `${domainDetails.domainName || 'Unknown'}.lk`}
            </h2>
            <p className="domain-description mb-3">
              {domainDetails.domainDescription || 'No description available.'}
            </p>
          </div>

          {domainDetails.relatedFields && domainDetails.relatedFields.length > 0 && (
            <div className="related-fields mb-5">
              <h2 className="section-heading mb-3">Related Fields</h2>
              <ul className="fields-list">
                {domainDetails.relatedFields.map((field, index) => (
                  <li key={index} className="field-item">
                    <span className="field-badge">- {field}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="domain-cta mt-4 text-center">
            <a
              href='https://www.domains.lk/'
              className="btn btn-primary domain-link-btn"
              target="_blank"
              rel="noopener noreferrer"
            >
              Visit domains.lk
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DomainDetails;