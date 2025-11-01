import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle, UploadCloud, ChevronLeft, FileText, Check } from 'lucide-react';

// --- Step Content Components ---

// Step 1: Upload Invoice
const UploadStep = ({ uploadedFile, fileError, isDragging, handleDragEnter, handleDragLeave, handleDrop, handleFileSelect }) => {
    
    // Determine the content based on file status
    let content;

    if (uploadedFile) {
        content = (
            <div className="flex flex-col items-center">
                <div className="text-center p-6 border-2 border-green-400 bg-green-50 rounded-lg w-full max-w-sm mx-auto shadow-inner">
                    <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                    <p className="text-md font-semibold text-green-700">File Uploaded Successfully</p>
                    <p className="text-sm text-gray-600 truncate mt-1">
                        <FileText className="inline w-4 h-4 mr-1 align-sub" />
                        {uploadedFile.name}
                    </p>
                    {/* 移除 XML Validation 按钮和相关提示 */}
                </div>
            </div>
        );
    } else {
        // Drag and Drop Area
        const dropzoneClasses = `transition-all duration-300 p-12 border-2 border-dashed rounded-xl cursor-pointer w-full max-w-xl mx-auto ${
            fileError
                ? 'border-red-500 bg-red-50'
                : isDragging
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400 bg-white hover:bg-gray-50'
        }`;

        content = (
            <div
                className={dropzoneClasses}
                onDragOver={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input').click()}
            >
                <input
                    id="file-input"
                    type="file"
                    accept="application/pdf,image/jpeg,image/png"
                    onChange={handleFileSelect}
                    className="hidden"
                />
                <div className="flex flex-col items-center justify-center text-center">
                    <UploadCloud className={`w-8 h-8 mb-3 ${fileError ? 'text-red-500' : 'text-gray-500'}`} />
                    <p className="text-lg font-medium text-gray-700">Drag & Drop or Click to Upload</p>
                    <p className="text-sm text-gray-500 mt-1">PDF, JPG, or PNG files only (Max 10MB)</p>
                    {fileError && (
                        <p className="text-sm text-red-600 font-semibold mt-2">{fileError}</p>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center pt-8">
            <h2 className="text-xl font-bold text-gray-800 mb-8">Upload Source Invoice</h2>
            {content}
        </div>
    );
};

// Step 2-5 Placeholder
const PlaceholderStep = ({ stepTitle, stepNumber }) => (
    <div className="p-8 text-center bg-gray-50 rounded-lg h-full flex flex-col items-center justify-center">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">{stepTitle}</h2>
        <p className="text-gray-600">
            This is Step {stepNumber}. The functionality for **{stepTitle}** will be developed here.
            <br />
            Currently, this is a blank placeholder page.
        </p>
    </div>
);


// --- Main Create Page Component ---

const steps = [
    { id: 1, name: 'Upload Invoice' },
    { id: 2, name: 'Information Confirmation' },
    { id: 3, name: 'XML Invoice Validation' },
    { id: 4, name: 'Review & Modify' },
    { id: 5, name: 'Send Invoice' },
];

const CreatePage = () => {
    const [currentStep, setCurrentStep] = useState(1);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [fileError, setFileError] = useState('');
    const [isDragging, setIsDragging] = useState(false);

    // --- File Handling Logic ---

    // 修复 Bug：不需要 isXmlValidated, isXmlValidating 状态
    
    const validateFile = (file) => {
        if (!file) {
            setFileError('Please select a file.');
            return false;
        }
        if (file.size > 10 * 1024 * 1024) { // Max 10MB
            setFileError('File size exceeds 10MB limit.');
            return false;
        }
        const validTypes = ['application/pdf', 'image/jpeg', 'image/png'];
        if (!validTypes.includes(file.type)) {
            setFileError('Invalid file type. Only PDF, JPG, or PNG are allowed.');
            return false;
        }
        setFileError('');
        return true;
    };

    const handleFileUpload = (file) => {
        if (validateFile(file)) {
            // 在实际应用中，这里应该调用后端 API 上传文件
            setUploadedFile(file);
            return true;
        }
        return false;
    };

    const handleFileSelect = (event) => {
        const file = event.target.files[0];
        handleFileUpload(file);
    };

    const handleDragEnter = useCallback((event) => {
        event.preventDefault();
        event.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((event) => {
        event.preventDefault();
        event.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((event) => {
        event.preventDefault();
        event.stopPropagation();
        setIsDragging(false);
        if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
            handleFileUpload(event.dataTransfer.files[0]);
            event.dataTransfer.clearData();
        }
    }, []);

    // --- Navigation Logic ---

    const goToNextStep = () => {
        if (currentStep < steps.length) {
            setCurrentStep(currentStep + 1);
        }
    };

    const goToPreviousStep = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    const isNextDisabled = () => {
        if (currentStep === steps.length) return true;
        
        // 简化逻辑：步骤 1 只需要上传文件即可进入下一步
        if (currentStep === 1) {
            return !uploadedFile; 
        }

        // 默认：启用下一步按钮
        return false;
    };


    // --- Content Rendering ---

    const renderStepContent = () => {
        switch (currentStep) {
            case 1:
                return <UploadStep
                    uploadedFile={uploadedFile}
                    fileError={fileError}
                    isDragging={isDragging}
                    handleDragEnter={handleDragEnter}
                    handleDragLeave={handleDragLeave}
                    handleDrop={handleDrop}
                    handleFileSelect={handleFileSelect}
                />;
            case 2:
                return <PlaceholderStep stepTitle={steps[1].name} stepNumber={2} />;
            case 3:
                return <PlaceholderStep stepTitle={steps[2].name} stepNumber={3} />;
            case 4:
                return <PlaceholderStep stepTitle={steps[3].name} stepNumber={4} />;
            case 5:
                return <PlaceholderStep stepTitle={steps[4].name} stepNumber={5} />;
            default:
                return <PlaceholderStep stepTitle="Unknown Step" stepNumber={currentStep} />;
        }
    };

    // --- UI Structure ---

    return (
        <div className="flex h-screen bg-gray-50">
            
            {/* Left Sidebar for Steps */}
            <aside className="w-64 flex flex-col justify-between bg-white p-6 shadow-lg border-r border-gray-200">
                <div>
                    <h1 className="text-xl font-bold text-gray-800 mb-8">E-Invoice Creation</h1>
                    
                    {/* Step Indicators */}
                    <div className="space-y-4">
                        {steps.map((step) => {
                            const isCurrent = step.id === currentStep;
                            const isDone = step.id < currentStep;
                            
                            // Color logic: Done (Green), Current (Blue), Pending (Gray)
                            const circleColor = isDone ? 'bg-green-500' : isCurrent ? 'bg-blue-600' : 'bg-gray-400';
                            const textColor = isDone ? 'text-gray-700' : isCurrent ? 'text-blue-600 font-semibold' : 'text-gray-500';

                            return (
                                <div key={step.id} className="flex items-center">
                                    <button 
                                        onClick={() => setCurrentStep(step.id)}
                                        className="flex items-center w-full text-left focus:outline-none group"
                                        // 移除 disabled={isCurrent}，允许点击当前步骤
                                    >
                                        {/* Step Circle */}
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm transition-colors duration-300 ${circleColor}`}>
                                            {isDone ? <Check className="w-4 h-4" /> : step.id}
                                        </div>
                                        {/* Step Name */}
                                        <p className={`ml-3 text-sm transition-colors duration-300 ${textColor} group-hover:text-blue-600`}>
                                            {step.name}
                                        </p>
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>

                {/* Back to Welcome Button/Link */}
                <div className="pt-6 border-t border-gray-200">
                    <Link 
                        to="/" 
                        className="text-sm font-semibold text-gray-600 hover:text-blue-600 transition-colors flex items-center p-2 rounded-lg bg-gray-50 hover:bg-gray-100 shadow-sm"
                    >
                        <ChevronLeft className="w-4 h-4 mr-1" />
                        Back to Welcome Page
                    </Link>
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 flex flex-col">
                <div className="flex-1 p-8 overflow-y-auto">
                    {/* Render current step content */}
                    {renderStepContent()}
                </div>

                {/* Bottom Navigation */}
                <footer className="p-4 bg-white border-t border-gray-200 flex justify-between items-center shadow-lg">
                    {/* Previous Button */}
                    <button
                        onClick={goToPreviousStep}
                        disabled={currentStep === 1}
                        className={`px-6 py-2 rounded-lg font-semibold transition-colors duration-200 shadow-md ${
                            currentStep === 1
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                    >
                        Previous
                    </button>

                    {/* Current Step Info */}
                    <span className="text-sm font-medium text-gray-600">
                        Step {currentStep} of {steps.length}: {steps[currentStep - 1].name}
                    </span>

                    {/* Next Button */}
                    <button
                        onClick={goToNextStep}
                        disabled={isNextDisabled()}
                        className={`px-6 py-2 rounded-lg font-semibold transition-colors duration-200 shadow-md ${
                            isNextDisabled()
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                    >
                        {currentStep === steps.length ? 'Finish' : 'Next'}
                    </button>
                </footer>
            </main>
        </div>
    );
};

export default CreatePage;