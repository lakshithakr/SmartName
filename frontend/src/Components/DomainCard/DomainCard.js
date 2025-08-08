import React from "react";
import "./DomainCard.css";
import { useNavigate } from "react-router-dom";

const DomainCard = ({ domainName, description, isLoading }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    sessionStorage.setItem("selectedDomain", domainName);
    // If we have a description, cache it for the details page
    if (description) {
      sessionStorage.setItem("selectedDomainDescription", JSON.stringify(description));
    }
    navigate("/details");
  };

  return (
    <div className="domain-card" onClick={handleClick}>
      <div className="domain-card-header">
        <h5 className="domain-name">{domainName}.lk</h5>
        <span className="availability-badge">Available</span>
      </div>
      
      <div className="domain-card-body">
        {isLoading ? (
          <div className="description-loading">
            <div className="description-skeleton">
              <div className="skeleton-line"></div>
              <div className="skeleton-line short"></div>
            </div>
            <p className="loading-text">Generating description...</p>
          </div>
        ) : description ? (
          <div className="domain-description">
            <p className="description-text">
              {description.domainDescription}
            </p>
            {description.relatedFields && description.relatedFields.length > 0 && (
              <div className="related-fields">
                <div className="fields-container">
                  {description.relatedFields.slice(0, 3).map((field, index) => (
                    <span key={index} className="field-tag">
                      {field}
                    </span>
                  ))}
                  {description.relatedFields.length > 3 && (
                    <span className="field-tag more">
                      +{description.relatedFields.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="no-description">
            <p className="description-placeholder">
              Click to view detailed information about this domain
            </p>
          </div>
        )}
      </div>
      
      <div className="domain-card-footer">
        <button className="view-details-btn">
          View Details →
        </button>
      </div>
    </div>
  );
};

export default DomainCard;