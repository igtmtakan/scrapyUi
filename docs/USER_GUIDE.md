# 📖 ScrapyUI User Guide

## 🎯 Getting Started

### 🚀 First Steps

1. **Access ScrapyUI**: Open http://localhost:4000 in your browser
2. **Login**: Use default credentials (admin@scrapyui.com / admin123456)
3. **Create Project**: Click "New Project" to start
4. **Add Spider**: Create your first spider using templates
5. **Run & Monitor**: Execute spiders and monitor progress in real-time

### 🏠 Dashboard Overview

The dashboard provides:
- **📊 Statistics**: Total projects, spiders, and tasks
- **📈 Recent Activity**: Latest task executions
- **🎯 Quick Actions**: Fast access to common operations
- **📋 Project Overview**: Summary of all projects

## 📁 Project Management

### Creating Projects

1. Click **"New Project"** button
2. Enter project details:
   - **Name**: Unique project identifier
   - **Description**: Project purpose and scope
3. Click **"Create"** to save

### Project Structure

Each project contains:
- **🕷️ Spiders**: Web scraping scripts
- **📋 Tasks**: Execution history
- **⚙️ Settings**: Project configuration
- **📊 Results**: Scraped data

### Project Settings

Configure project-wide settings:
- **Scrapy Settings**: DOWNLOAD_DELAY, CONCURRENT_REQUESTS
- **Playwright Settings**: Browser type, headless mode
- **Output Settings**: File formats, storage location

## 🕷️ Spider Development

### Using Templates

ScrapyUI provides 50+ pre-built templates:

#### 🛒 E-commerce Templates
- **Amazon Product Scraper**: Extract product details
- **Rakuten Store Scraper**: Scrape store information
- **Yahoo Shopping**: Product listings and prices

#### 📰 News Templates
- **Yahoo News Sports**: Sports articles and scores
- **General News**: Article headlines and content

#### 🍽️ Food & Restaurant Templates
- **Gurunavi**: Restaurant information and reviews
- **Food Delivery**: Menu items and prices

### Code Editor Features

The Monaco Editor provides:
- **🎨 Syntax Highlighting**: Python and Scrapy syntax
- **🔍 IntelliSense**: Auto-completion and suggestions
- **🐛 Error Detection**: Real-time error highlighting
- **📁 File Management**: Multi-file editing support

### Spider Templates Structure

```python
import scrapy
from scrapy_playwright.page import PageMethod

class ExampleSpider(scrapy.Spider):
    name = 'example_spider'
    start_urls = ['https://example.com']
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'PLAYWRIGHT_BROWSER_TYPE': 'chromium',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True},
    }
    
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'domcontentloaded'),
                    ],
                }
            )
    
    def parse(self, response):
        # Extract data using CSS selectors
        for item in response.css('.item'):
            yield {
                'title': item.css('.title::text').get(),
                'price': item.css('.price::text').get(),
                'url': item.css('a::attr(href)').get(),
            }
        
        # Follow pagination
        next_page = response.css('.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
```

## 🚀 Running Spiders

### Quick Run

1. Navigate to spider page
2. Click **"Run"** button
3. Monitor progress in real-time
4. View results when complete

### Advanced Execution

Configure execution settings:
- **Custom Settings**: Override default Scrapy settings
- **Arguments**: Pass spider arguments
- **Scheduling**: Set execution time
- **Notifications**: Email alerts on completion

### Monitoring Execution

Real-time monitoring shows:
- **📊 Progress Bar**: Completion percentage
- **📈 Statistics**: Items scraped, requests made
- **🕐 Timing**: Start time, duration, ETA
- **🚨 Errors**: Error count and details

## 📊 Results & Export

### Viewing Results

Results are displayed in:
- **📋 Table View**: Structured data table
- **🔍 JSON View**: Raw JSON format
- **📈 Chart View**: Visual data representation

### Export Formats

Export data in multiple formats:
- **📄 JSON**: Machine-readable format
- **📊 CSV**: Spreadsheet compatible
- **📈 Excel**: Advanced spreadsheet format
- **🔖 XML**: Structured markup format

### Download Results

1. Go to task results page
2. Select export format
3. Click **"Download"** button
4. File downloads automatically

## ⚙️ Settings & Configuration

### User Settings

Customize your experience:
- **🎨 Theme**: Light/dark mode
- **🔔 Notifications**: Email preferences
- **🌐 Language**: Interface language
- **⏰ Timezone**: Local time display

### System Settings

Admin users can configure:
- **🗄️ Database**: Connection settings
- **🔐 Authentication**: JWT settings
- **📧 Email**: SMTP configuration
- **🐳 Docker**: Container settings

## 🔧 Advanced Features

### Scrapy Shell Integration

Interactive debugging:
1. Click **"Shell"** button
2. Enter Scrapy shell commands
3. Test selectors and responses
4. Debug spider logic

### Template Customization

Create custom templates:
1. Develop spider code
2. Save as template
3. Share with team
4. Reuse across projects

### API Integration

Use REST API for:
- **🤖 Automation**: Programmatic control
- **📊 Integration**: External systems
- **📈 Monitoring**: Custom dashboards
- **🔄 Workflows**: CI/CD pipelines

## 🚨 Troubleshooting

### Common Issues

#### Spider Not Starting
- Check spider syntax
- Verify start_urls
- Review error logs

#### No Data Extracted
- Test CSS selectors
- Check page loading
- Verify response content

#### Performance Issues
- Adjust DOWNLOAD_DELAY
- Reduce CONCURRENT_REQUESTS
- Enable AutoThrottle

### Error Messages

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError` | Install missing dependencies |
| `TimeoutError` | Increase timeout settings |
| `403 Forbidden` | Check robots.txt and headers |
| `Memory Error` | Reduce concurrent requests |

### Getting Help

- **📚 Documentation**: Check API docs
- **🐛 Issues**: Report on GitHub
- **💬 Community**: Join discussions
- **📧 Support**: Contact admin@scrapyui.com

## 🎓 Best Practices

### Spider Development
- Use descriptive names
- Add comments and documentation
- Handle errors gracefully
- Respect robots.txt

### Performance Optimization
- Set appropriate delays
- Use efficient selectors
- Implement data validation
- Monitor resource usage

### Data Quality
- Validate extracted data
- Handle missing values
- Normalize data formats
- Remove duplicates

### Security
- Use secure connections
- Rotate user agents
- Implement rate limiting
- Respect website terms
