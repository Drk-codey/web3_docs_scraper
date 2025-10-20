import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import axios from 'axios';
import { ArrowLeft, Calendar, ExternalLink, FileText, Download, Copy, Check, Home, Code, BookOpen, Settings, Zap } from 'lucide-react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

export default function SummaryDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    if (id) {
      fetchSummary(id);
    }
  }, [id]);

  const fetchSummary = async (summaryId) => {
    try {
      setLoading(true);
      const res = await axios.get(`${BACKEND_URL}/summaries/${summaryId}`);
      setSummary(res.data);
      
      // Set page title
      if (res.data && res.data.title) {
        document.title = `${res.data.title} - Web3 Docs Scraper`;
      }
    } catch (err) {
      setError('Failed to load summary details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const downloadSummary = () => {
    if (!summary) return;
    
    const element = document.createElement('a');
    const file = new Blob([summary.summary], { type: 'text/markdown' });
    element.href = URL.createObjectURL(file);
    element.download = `${summary.title.toLowerCase().replace(/\s+/g, '-')}-summary.md`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const copyToClipboard = async () => {
    if (!summary) return;
    
    try {
      await navigator.clipboard.writeText(summary.summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  // Extract sections from the summary for navigation
  const extractSections = (summaryText) => {
    if (!summaryText) return [];
    
    const sections = [];
    const lines = summaryText.split('\n');
    
    lines.forEach(line => {
      if (line.startsWith('## ')) {
        const title = line.substring(3).trim();
        // Extract emoji and text
        const emojiMatch = title.match(/^([^\w\s]+\s?)/);
        const emoji = emojiMatch ? emojiMatch[0].trim() : '📄';
        const cleanTitle = title.replace(/^([^\w\s]+\s?)/, '').trim();
        
        const id = cleanTitle.toLowerCase().replace(/\s+/g, '-');
        
        sections.push({
          id,
          title: cleanTitle,
          emoji,
          level: 2
        });
      } else if (line.startsWith('### ')) {
        const title = line.substring(4).trim();
        const id = title.toLowerCase().replace(/\s+/g, '-');
        
        sections.push({
          id,
          title,
          emoji: '•',
          level: 3
        });
      }
    });
    
    return sections;
  };

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
      setActiveSection(sectionId);
    }
  };

  const renderMarkdown = (text) => {
    if (!text) return '';
    
    return text.split('\n').map((line, index) => {
      // Main title
      if (line.startsWith('# ') && !line.startsWith('##')) {
        return <h1 key={index} className="text-4xl font-bold text-white mb-5 mt-2">{line.substring(2)}</h1>;
      }
      
      // Section headers with emojis
      if (line.startsWith('## ')) {
        const title = line.substring(3);
        const id = title.replace(/^([^\w\s]+\s?)/, '').trim().toLowerCase().replace(/\s+/g, '-');
        return (
          <h2 
            key={index} 
            id={id}
            className="text-2xl font-bold text-white mt-8 mb-4 pb-2 border-b border-gray-700"
          >
            {title}
          </h2>
        );
      }
      
      // Subsection headers
      if (line.startsWith('### ')) {
        const title = line.substring(4);
        const id = title.toLowerCase().replace(/\s+/g, '-');
        return (
          <h3 
            key={index} 
            id={id}
            className="text-xl font-semibold text-gray-200 mt-6 mb-3"
          >
            {title}
          </h3>
        );
      }
      
      // Bold text
      if (line.includes('**') && line.split('**').length >= 3) {
        const parts = line.split('**');
        const elements = [];
        parts.forEach((part, i) => {
          if (i % 2 === 1) {
            elements.push(<strong key={i} className="text-white font-semibold">{part}</strong>);
          } else if (part) {
            elements.push(part);
          }
        });
        return <p key={index} className="mb-4 text-gray-300 leading-relaxed">{elements}</p>;
      }
      
      // Lists
      if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) {
        return (
          <li key={index} className="ml-6 mb-2 text-gray-300 leading-relaxed flex items-start">
            <span className="text-indigo-400 mr-2 mt-1">•</span>
            <span>{line.substring(2)}</span>
          </li>
        );
      }
      
      // Numbered lists
      if (/^\d+\.\s/.test(line)) {
        const match = line.match(/^(\d+)\.\s(.*)/);
        return (
          <li key={index} className="ml-6 mb-2 text-gray-300 leading-relaxed flex items-start">
            <span className="text-indigo-400 mr-2 mt-1 font-semibold">{match[1]}.</span>
            <span>{match[2]}</span>
          </li>
        );
      }
      
      // Code blocks (simple detection)
      if (line.trim().startsWith('```') || line.includes('`')) {
        const codeMatch = line.match(/`([^`]+)`/);
        if (codeMatch) {
          return (
            <code key={index} className="bg-gray-700 text-green-400 px-2 py-1 rounded text-sm font-mono">
              {codeMatch[1]}
            </code>
          );
        }
      }
      
      // Horizontal rule
      if (line.trim() === '---' || line.trim() === '***') {
        return <hr key={index} className="my-6 border-gray-700" />;
      }
      
      // Empty line
      if (line.trim() === '') {
        return <br key={index} />;
      }
      
      // Metadata lines (bold labels)
      if (line.includes('**Source:**') || line.includes('**Generated:**') || line.includes('**AI Model:**')) {
        return <p key={index} className="text-gray-400 text-sm mb-2">{line}</p>;
      }
      
      // Regular paragraph
      return <p key={index} className="mb-4 text-gray-300 leading-relaxed">{line}</p>;
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading comprehensive documentation summary...</p>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-4">
            <p className="text-red-400 text-xl">{error || 'Summary not found'}</p>
          </div>
          <button
            onClick={() => router.push('/')}
            className="bg-indigo-600 px-6 py-3 rounded-xl hover:bg-indigo-500 transition flex items-center gap-2 mx-auto"
          >
            <Home className="w-5 h-5" />
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const sections = extractSections(summary.summary);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition"
            >
              <ArrowLeft className="w-5 h-5" />
              Back to summaries
            </button>
            
            <div className="flex gap-3">
              <button
                onClick={copyToClipboard}
                className="bg-blue-600 px-4 py-2 rounded-lg hover:bg-blue-500 transition flex items-center gap-2"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              <button
                onClick={downloadSummary}
                className="bg-green-600 px-4 py-2 rounded-lg hover:bg-green-500 transition flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>
          </div>

          <div className="bg-gray-800/50 rounded-2xl p-8 backdrop-blur-sm border border-gray-700">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent mb-4">
                  {summary.title}
                </h1>

                <div className="flex flex-wrap items-center gap-4 text-gray-400 mb-4">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>{new Date(summary.created_at).toLocaleDateString('en-US', { 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <ExternalLink className="w-4 h-4" />
                    <a
                      href={summary.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:text-indigo-400 transition break-all max-w-md truncate"
                      title={summary.url}
                    >
                      {summary.url}
                    </a>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    <span>ID: {summary.id}</span>
                  </div>
                </div>

                <p className="text-gray-300 text-lg leading-relaxed">
                  Comprehensive documentation summary generated using advanced AI models. 
                  This summary provides all the essential information developers need to understand and work with this technology.
                </p>
              </div>
              
              <div className="ml-6 flex-shrink-0 max-sm:hidden">
                <div className="bg-indigo-500/20 border border-indigo-500/30 rounded-xl p-4 text-center">
                  <Zap className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
                  <div className="text-sm text-indigo-300">AI Generated</div>
                  <div className="text-xs text-gray-400">Comprehensive</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-8 max-md:flex-col">
          {/* Table of Contents */}
          {sections.length > 0 && (
            <div className="w-64 flex-shrink-0">
              <div className="bg-gray-800/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-700 sticky top-8">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  Contents
                </h3>
                <nav className="space-y-2">
                  {sections.map((section) => (
                    <button
                      key={section.id}
                      onClick={() => scrollToSection(section.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition text-sm ${
                        activeSection === section.id
                          ? 'bg-indigo-600 text-white'
                          : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                      } ${section.level === 3 ? 'ml-4 text-xs' : ''}`}
                    >
                      <span className="mr-2">{section.emoji}</span>
                      {section.title}
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          )}

          {/* Summary Content */}
          <div className="flex-1">
            <div className="bg-gray-800/50 rounded-2xl p-8 backdrop-blur-sm border border-gray-700">
              <div className="prose prose-invert max-w-none">
                <div className="text-gray-300 leading-relaxed">
                  {renderMarkdown(summary.summary)}
                </div>
              </div>
            </div>

            {/* Technical Details */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-800/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <Code className="w-6 h-6 text-green-400" />
                  <h3 className="text-lg font-semibold text-white">Content Stats</h3>
                </div>
                <div className="space-y-2 text-sm text-gray-300">
                  <div className="flex justify-between">
                    <span>Original Content:</span>
                    <span className="text-white">{summary.content.length.toLocaleString()} chars</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Summary Length:</span>
                    <span className="text-white">{summary.summary.length.toLocaleString()} chars</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Sections:</span>
                    <span className="text-white">{sections.length}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <Settings className="w-6 h-6 text-blue-400" />
                  <h3 className="text-lg font-semibold text-white">Quick Actions</h3>
                </div>
                <div className="space-y-3">
                  <button
                    onClick={downloadSummary}
                    className="w-full bg-green-600 hover:bg-green-500 transition text-white py-2 rounded-lg flex items-center justify-center gap-2 text-sm"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                  <button
                    onClick={copyToClipboard}
                    className="w-full bg-blue-600 hover:bg-blue-500 transition text-white py-2 rounded-lg flex items-center justify-center gap-2 text-sm"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    {copied ? 'Copied!' : 'Copy to Clipboard'}
                  </button>
                </div>
              </div>

              <div className="bg-gray-800/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-700">
                <div className="flex items-center gap-3 mb-4">
                  <ExternalLink className="w-6 h-6 text-purple-400" />
                  <h3 className="text-lg font-semibold text-white">Source</h3>
                </div>
                <a
                  href={summary.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-indigo-400 hover:text-indigo-300 transition text-sm break-all mb-4"
                >
                  {summary.url}
                </a>
                <p className="text-gray-400 text-xs">
                  Visit the original documentation for complete details and latest updates.
                </p>
              </div>
            </div>

            {/* Original Content Preview */}
            <div className="mt-8 bg-gray-800/50 rounded-2xl p-6 backdrop-blur-sm border border-gray-700">
              <h2 className="text-2xl font-bold text-gray-300 mb-4 flex items-center gap-2">
                <FileText className="w-6 h-6 text-yellow-400" />
                Original Content Preview
              </h2>
              <div className="prose prose-invert max-w-none">
                <div className="bg-gray-900/50 rounded-xl p-4 border border-gray-700">
                  <p className="text-gray-400 whitespace-pre-wrap leading-relaxed text-sm">
                    {summary.content.substring(0, 2000)}...
                  </p>
                </div>
              </div>
              <p className="text-gray-500 text-sm mt-4">
                Preview showing first 2000 characters. Full content available in the database.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}