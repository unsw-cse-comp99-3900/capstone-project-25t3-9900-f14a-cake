import React, { useState, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle,
  UploadCloud,
  ChevronLeft,
  FileText,
  Check,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

// =================== Step 1: 上传 ===================
const UploadStep = ({
  uploadedFile,
  fileError,
  isDragging,
  handleDragEnter,
  handleDragLeave,
  handleDrop,
  handleFileSelect,
}) => {
  let content;

  if (uploadedFile) {
    content = (
      <div className="flex flex-col items-center">
        <div className="text-center p-6 border-2 border-green-400 bg-green-50 rounded-lg w-full max-w-sm mx-auto shadow-inner">
          <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
          <p className="text-md font-semibold text-green-700">
            File Uploaded Successfully
          </p>
          <p className="text-sm text-gray-600 truncate mt-1">
            <FileText className="inline w-4 h-4 mr-1 align-sub" />
            {uploadedFile.name}
          </p>
        </div>
      </div>
    );
  } else {
    const dropzoneClasses = `transition-all duration-300 p-12 border-2 border-dashed rounded-xl cursor-pointer w-full max-w-xl mx-auto ${
      fileError
        ? "border-red-500 bg-red-50"
        : isDragging
        ? "border-blue-500 bg-blue-50"
        : "border-gray-300 hover:border-blue-400 bg-white hover:bg-gray-50"
    }`;

    content = (
      <div
        className={dropzoneClasses}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => document.getElementById("file-input").click()}
      >
        <input
          id="file-input"
          type="file"
          accept="application/pdf,image/jpeg,image/png"
          onChange={handleFileSelect}
          className="hidden"
        />
        <div className="flex flex-col items-center justify-center text-center">
          <UploadCloud
            className={`w-8 h-8 mb-3 ${
              fileError ? "text-red-500" : "text-gray-500"
            }`}
          />
          <p className="text-lg font-medium text-gray-700">
            Drag & Drop or Click to Upload
          </p>
          <p className="text-sm text-gray-500 mt-1">
            PDF, JPG, or PNG files only (Max 10MB)
          </p>
          {fileError && (
            <p className="text-sm text-red-600 font-semibold mt-2">
              {fileError}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center pt-8">
      <h2 className="text-xl font-bold text-gray-800 mb-8">
        Upload Source Invoice
      </h2>
      {content}
    </div>
  );
};

// =================== Step 2: 信息确认（可编辑） ===================
const InfoConfirmStep = ({ summary, xmlPreview, onSummaryChange, onUpdateXML }) => {
  if (!summary) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <p>No invoice data yet. Please upload a file in Step 1.</p>
      </div>
    );
  }

  const handleChange = (field, value) => {
    onSummaryChange({
      ...summary,
      [field]: value,
    });
  };

  const editableFields = [
    { label: "Document Type", field: "document_type", type: "text" },
    { label: "Document Title", field: "document_title", type: "text" },
    { label: "Invoice Number", field: "invoice_number", type: "text" },
    { label: "Reference Number", field: "reference_number", type: "text" },
    { label: "Issue Date", field: "issue_date", type: "date" },
    { label: "Due Date", field: "due_date", type: "date" },
    { label: "Currency Code", field: "currency_code", type: "text" },
    { label: "Subtotal", field: "subtotal", type: "number" },
    { label: "Tax", field: "tax", type: "number" },
    { label: "Total", field: "total", type: "number" },
    { label: "Country Code", field: "country_code", type: "text" },
    { label: "Created Date", field: "created_date", type: "date" },
  ];

  return (
    <div className="bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-xl font-bold text-gray-800 mb-6">
        Invoice Information
      </h2>

      <div className="grid grid-cols-2 gap-4 text-sm">
        {editableFields.map(({ label, field, type }) => (
          <label key={field} className="flex flex-col">
            <b>{label}:</b>
            <input
              type={type}
              value={summary[field] || ""}
              onChange={(e) => handleChange(field, e.target.value)}
              className="mt-1 p-2 border border-gray-300 rounded"
            />
          </label>
        ))}
      </div>

      {xmlPreview && (
        <div className="mt-6">
          <h3 className="text-md font-semibold text-gray-700 mb-2">
            XML Preview:
          </h3>
          <textarea
            readOnly
            value={xmlPreview}
            className="w-full h-64 text-xs font-mono bg-gray-50 border border-gray-200 rounded-lg p-2"
          />
        </div>
      )}

      <div className="mt-4 flex justify-end space-x-3">
        <button
          onClick={() => onUpdateXML(summary)}
          className="flex items-center bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4 mr-2" /> Refresh XML
        </button>
      </div>
    </div>
  );
};

// =================== 主组件 ===================
const steps = [
  { id: 1, name: "Upload Invoice" },
  { id: 2, name: "Information Confirmation" },
  { id: 3, name: "XML Invoice Validation" },
  { id: 4, name: "Review & Modify" },
  { id: 5, name: "Send Invoice" },
];

const CreatePage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileError, setFileError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [invoiceSummary, setInvoiceSummary] = useState(null);
  const [xmlPreview, setXmlPreview] = useState("");

  const validateFile = (file) => {
    if (!file) return setFileError("Please select a file."), false;
    if (file.size > 10 * 1024 * 1024)
      return setFileError("File size exceeds 10MB limit."), false;
    if (!["application/pdf", "image/jpeg", "image/png"].includes(file.type)) {
      return (
        setFileError("Invalid file type. Only PDF, JPG, or PNG are allowed."),
        false
      );
    }
    setFileError("");
    return true;
  };

  const handleFileUpload = async (file) => {
    if (!validateFile(file)) return false;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const uploadResp = await fetch("http://localhost:5001/api/upload", {
        method: "POST",
        body: formData,
      });
      const uploadData = await uploadResp.json();
      if (!uploadResp.ok) throw new Error(uploadData.error || "Upload failed");
      setUploadedFile(file);

      const convertResp = await fetch("http://localhost:5001/api/convert_to_xml", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(uploadData.veryfi_result ?? uploadData ?? {}),
      });

      const convertData = await convertResp.json();
      if (convertResp.ok) {
        setInvoiceSummary(convertData.summary);
        setXmlPreview(convertData.xml_preview);
      } else setFileError(convertData.error || "XML conversion failed");
    } catch (err) {
      setFileError("Server not reachable");
    }
  };

  const handleUpdateXML = async (updatedSummary) => {
    try {
      const resp = await fetch("http://localhost:5001/api/update_xml", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedSummary),
      });
      const data = await resp.json();
      if (resp.ok) {
        setXmlPreview(data.xml_preview);
        console.log("✅ XML updated:", data);
      } else {
        console.error("❌ XML update failed:", data.error);
      }
    } catch (err) {
      console.error("❌ XML update error:", err);
    }
  };

  const handleFileSelect = (e) => handleFileUpload(e.target.files[0]);
  const handleDragEnter = useCallback((e) => { e.preventDefault(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e) => { e.preventDefault(); setIsDragging(false); }, []);
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length) handleFileUpload(e.dataTransfer.files[0]);
  }, []);

  const goToNextStep = () => currentStep < steps.length && setCurrentStep(currentStep + 1);
  const goToPreviousStep = () => currentStep > 1 && setCurrentStep(currentStep - 1);
  const isNextDisabled = () => currentStep === 1 && !uploadedFile;

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <UploadStep
            {...{ uploadedFile, fileError, isDragging, handleDragEnter, handleDragLeave, handleDrop, handleFileSelect }}
          />
        );
      case 2:
        return (
          <InfoConfirmStep
            summary={invoiceSummary}
            xmlPreview={xmlPreview}
            onSummaryChange={setInvoiceSummary}
            onUpdateXML={handleUpdateXML}
          />
        );
      default:
        return <div className="text-center text-gray-500 mt-20">Step not implemented yet.</div>;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col justify-between bg-white p-6 shadow-lg border-r border-gray-200">
        <div>
          <h1 className="text-xl font-bold text-gray-800 mb-8">
            E-Invoice Creation
          </h1>
          <div className="space-y-4">
            {steps.map((step) => {
              const isCurrent = step.id === currentStep;
              const isDone = step.id < currentStep;
              const circleColor = isDone
                ? "bg-green-500"
                : isCurrent
                ? "bg-blue-600"
                : "bg-gray-400";
              const textColor = isDone
                ? "text-gray-700"
                : isCurrent
                ? "text-blue-600 font-semibold"
                : "text-gray-500";
              return (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => setCurrentStep(step.id)}
                    className="flex items-center w-full text-left focus:outline-none group"
                  >
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${circleColor}`}
                    >
                      {isDone ? <Check className="w-4 h-4" /> : step.id}
                    </div>
                    <p
                      className={`ml-3 text-sm ${textColor} group-hover:text-blue-600`}
                    >
                      {step.name}
                    </p>
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        <div className="pt-6 border-t border-gray-200">
          <Link
            to="/"
            className="text-sm font-semibold text-gray-600 hover:text-blue-600 flex items-center p-2 rounded-lg bg-gray-50 hover:bg-gray-100 shadow-sm"
          >
            <ChevronLeft className="w-4 h-4 mr-1" /> Back to Welcome Page
          </Link>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col">
        <div className="flex-1 p-8 overflow-y-auto">{renderStepContent()}</div>
        <footer className="p-4 bg-white border-t border-gray-200 flex justify-between items-center shadow-lg">
          <button
            onClick={goToPreviousStep}
            disabled={currentStep === 1}
            className={`px-6 py-2 rounded-lg font-semibold ${
              currentStep === 1
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Previous
          </button>
          <span className="text-sm font-medium text-gray-600">
            Step {currentStep} of {steps.length}: {steps[currentStep - 1].name}
          </span>
          <button
            onClick={goToNextStep}
            disabled={isNextDisabled()}
            className={`px-6 py-2 rounded-lg font-semibold ${
              isNextDisabled()
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700"
            }`}
          >
            {currentStep === steps.length ? "Finish" : "Next"}
          </button>
        </footer>
      </main>
    </div>
  );
};

export default CreatePage;
