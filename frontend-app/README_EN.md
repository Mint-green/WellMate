# WellMate Health Assistant App

## Project Introduction
WellMate is a comprehensive health assistant application that integrates physical health monitoring and mental health support functions, aiming to provide users with all-round health management services.

## Main Functions

### 1. Physical Health Assistant
- AI health consultation function, providing professional health advice
- Health data display (steps, sleep, heart rate, blood pressure, etc.)

### 2. Mental Health Support (Mind Tree Hole)
- AI psychological consultation service
- Emotional guidance and psychological support
- Message history and session management
- Voice playback function (to listen to AI replies)

### 3. Personal Center (Mine)
- User information management
- Application settings
- Language switching (supporting English/Chinese)
- Session history management

### 4. Overview Page
- Health data overview
- Quick access to various functions

## Technical Architecture

### Frontend Technology Stack
- **Framework**: uni-app x (high-performance cross-platform application development framework)
- **Development Language**: TypeScript (UTS)
- **UI Components**: Custom components + uni-app x built-in components
- **Internationalization**: Support for multi-language switching (English/Chinese)

## Project Structure

```
├── pages/                # Page components
│   ├── login/           # Login page
│   ├── register/        # Register page
│   ├── index/           # Overview page
│   ├── physical/        # Physical health assistant page
│   ├── mental/          # Mental health support page
│   ├── mine/            # Personal center page
│   └── settings/        # Settings page
├── utils/               # Utility functions and services
│   ├── api-service.uts  # API service encapsulation
│   ├── env-config.uts   # Environment configuration
│   └── i18n/            # Internationalization related
├── components/          # Public components
├── static/              # Static resources
├── App.uvue             # Application entry component
├── main.uts             # Application main configuration
└── pages.json           # Page routing configuration
```

## Core Function Modules

### 1. AI Conversation Function
- Supports two conversation types: physical health and mental health
- Message history saving
- Session management (creation, viewing, deletion)
- Voice playback function (for AI replies)

### 2. Health Data Management
- Support for monitoring multiple health indicators
- Third-party health data synchronization
- Data visualization display

### 3. Internationalization Support
- Automatically detect and apply user language preferences
- Support for English and Chinese switching
- Local storage of language settings

## Application Features

- **Cross-platform compatibility**: Supports iOS, Android, Web and other platforms
- **User-friendly interface**: Simple and intuitive interactive design
- **Data security**: User data protection and privacy security
- **Responsive design**: Adapts to different device screen sizes

## Development Guide

Please use the HBuilderX development tool to open the project folder for development and running:

1. Download and install [HBuilderX](https://www.dcloud.io/hbuilderx.html)
2. Use HBuilderX to open the project folder
3. Wait for dependencies to be automatically installed
4. Click the run button in the toolbar and select the corresponding runtime environment (H5)
5. When building the project, click the publish button in the toolbar and select the corresponding publishing platform