# CSV Analysis Shiny App
# 여러 CSV 파일을 업로드하여 분석하고 그래프를 생성하는 앱

library(shiny)
library(shinydashboard)
library(DT)
library(readxl)
library(tidyverse)
library(writexl)
library(stringr)
library(gt)
library(showtext) # 한글
library(viridis) #특정 color 묶음
library(patchwork)
library(purrr)
showtext_auto()

# UI
ui <- dashboardPage(
  dashboardHeader(title = "CSV 파일 분석 도구"),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("파일 업로드", tabName = "upload", icon = icon("upload")),
      menuItem("데이터 분석", tabName = "analysis", icon = icon("chart-line")),
      menuItem("결과 다운로드", tabName = "download", icon = icon("download"))
    )
  ),
  
  dashboardBody(
    tags$head(
      tags$style(HTML("
        .upload-area {
          border: 2px dashed #cccccc;
          border-radius: 10px;
          text-align: center;
          padding: 50px;
          margin: 20px 0;
          background-color: #f9f9f9;
          transition: all 0.3s ease;
        }
        .upload-area:hover {
          border-color: #007bff;
          background-color: #e3f2fd;
        }
        .file-input-button {
          background-color: #007bff;
          color: white;
          padding: 10px 20px;
          border: none;
          border-radius: 5px;
          cursor: pointer;
          font-size: 16px;
        }
      "))
    ),
    
    tabItems(
      # 파일 업로드 탭
      tabItem(tabName = "upload",
        fluidRow(
          box(
            title = "CSV 파일 업로드", 
            status = "primary", 
            solidHeader = TRUE,
            width = 12,
            div(class = "upload-area",
              h3("CSV 파일을 드래그 앤 드롭하거나 선택하세요"),
              br(),
              fileInput("files", 
                       label = NULL,
                       multiple = TRUE,
                       accept = c(".csv"),
                       buttonLabel = "파일 선택...",
                       placeholder = "선택된 파일이 없습니다"),
              br(),
              h5("여러 파일을 한번에 선택할 수 있습니다"),
              h6("지원 형식: CSV 파일")
            )
          )
        ),
        
        fluidRow(
          box(
            title = "업로드된 파일 목록", 
            status = "info", 
            solidHeader = TRUE,
            width = 12,
            DT::dataTableOutput("file_list")
          )
        )
      ),
      
      # 데이터 분석 탭
      tabItem(tabName = "analysis",
        fluidRow(
          box(
            title = "분석 설정", 
            status = "primary", 
            solidHeader = TRUE,
            width = 12,
            actionButton("analyze_btn", "분석 시작", 
                        class = "btn-primary btn-lg",
                        style = "margin: 10px;"),
            br(),br(),
            verbatimTextOutput("analysis_status")
          )
        ),
        
        fluidRow(
          box(
            title = "분석 결과 데이터", 
            status = "success", 
            solidHeader = TRUE,
            width = 12,
            DT::dataTableOutput("result_table")
          )
        ),
        
        fluidRow(
          box(
            title = "전체 그래프", 
            status = "success", 
            solidHeader = TRUE,
            width = 12,
            plotOutput("main_plot", height = "600px")
          )
        ),
        
        fluidRow(
          box(
            title = "위치별 SIP Profile", 
            status = "success", 
            solidHeader = TRUE,
            width = 6,
            plotOutput("profile_plot", height = "400px")
          ),
          
          box(
            title = "Hump Height vs Position", 
            status = "success", 
            solidHeader = TRUE,
            width = 6,
            plotOutput("hump_plot", height = "400px")
          )
        )
      ),
      
      # 결과 다운로드 탭
      tabItem(tabName = "download",
        fluidRow(
          box(
            title = "결과 다운로드", 
            status = "primary", 
            solidHeader = TRUE,
            width = 12,
            h4("분석이 완료된 후 결과를 다운로드할 수 있습니다."),
            br(),
            downloadButton("download_csv", "CSV 결과 다운로드", 
                          class = "btn-success",
                          style = "margin: 10px;"),
            br(),br(),
            downloadButton("download_plot", "그래프 PNG 다운로드", 
                          class = "btn-info",
                          style = "margin: 10px;"),
            br(),br(),
            h5("다운로드 상태:"),
            verbatimTextOutput("download_status")
          )
        )
      )
    )
  )
)

# Server
server <- function(input, output, session) {
  
  # 반응형 변수들
  values <- reactiveValues(
    df1 = NULL,
    result = NULL,
    plots = NULL,
    analysis_complete = FALSE
  )
  
  # 업로드된 파일 목록 표시
  output$file_list <- DT::renderDataTable({
    if (is.null(input$files)) {
      return(data.frame(파일명 = "업로드된 파일이 없습니다", 크기 = "", 타입 = ""))
    }
    
    file_info <- data.frame(
      파일명 = input$files$name,
      크기 = paste(round(input$files$size / 1024, 2), "KB"),
      타입 = input$files$type
    )
    file_info
  }, options = list(pageLength = 10, searching = FALSE))
  
  # 파일 읽기 및 데이터 처리
  observeEvent(input$analyze_btn, {
    if (is.null(input$files)) {
      output$analysis_status <- renderText("먼저 CSV 파일을 업로드해주세요.")
      return()
    }
    
    output$analysis_status <- renderText("분석을 시작합니다...")
    
    tryCatch({
      # 파일 읽기
      df_list <- map(input$files$datapath, ~read_csv(.x, show_col_types = FALSE))
      names(df_list) <- input$files$name
      
      values$df1 <- df_list %>%
        imap_dfr(~mutate(.x, file = .y))
      
      output$analysis_status <- renderText("데이터를 성공적으로 읽었습니다. 분석 중...")
      
      # 데이터 분석 로직 (원본 코드 기반)
      result1 <- values$df1 %>% 
        mutate(cell = str_sub(`CELL ID`, -3, -1)) %>% 
        mutate(position = str_sub(str_sub(file, -13, -1),1,1)) %>% 
        select(`Glass ID`, no, `Avg Offset`, cell, position) %>% 
        mutate(x = no*10.96) %>% 
        filter(position != "4") %>% 
        pivot_wider(names_from = c(`Glass ID`, cell, position), values_from = `Avg Offset`) %>% 
        mutate(across(c(3:ncol(.)), ~.x - .x[456])) %>% 
        pivot_longer(cols = c(3:ncol(.)), names_to = c("glass", "cell", "position"),  
                    names_sep = '_', values_to = "y") %>% 
        arrange(glass, cell, position, no) %>% 
        mutate(side = case_when(
          position == "1" ~ "Left",
          position == "2" ~ "Right",
          position == "3" ~ "Top",
          position == "4" ~ "Down"
        )) %>% 
        group_by(glass, cell, side) %>% 
        summarise(hump_dy = round(max(y, na.rm = TRUE), 1), 
                 hump_dx = round(10.96*which.max(y)), .groups = "drop") %>% 
        arrange(glass, cell, side) %>% 
        mutate(split = case_when(
          cell %in% c("A01", "B02", "C04", "D05", "A06", "B07", "C09", "D10") ~ "Sp1",
          cell %in% c("A03", "C03","A08", "C08") ~ "Sp2",
          cell %in% c("B03", "D03", "B08", "D08") ~ "Sp3"
        ))
      
      result2 <- values$df1 %>% 
        mutate(cell = str_sub(`CELL ID`, -3, -1)) %>% 
        mutate(position = str_sub(str_sub(file, -13, -1),1,1)) %>% 
        select(`Glass ID`, no, `Avg Offset`, cell, position) %>% 
        mutate(x = no*10.96) %>% 
        filter(position == "4") %>% 
        rename(glass = `Glass ID`, y = `Avg Offset`) %>% 
        mutate(side = case_when(
          position == "1" ~ "Left",
          position == "2" ~ "Right",
          position == "3" ~ "Top",
          position == "4" ~ "Down"
        )) %>% 
        group_by(glass, cell, side) %>% 
        summarise(hump_dy = round(max(y, na.rm = TRUE) - min(y, na.rm = TRUE), 1), 
                 hump_dx = round(10.96*which.max(y)), .groups = "drop") %>% 
        mutate(split = case_when(
          cell %in% c("A01", "B02", "C04", "D05", "A06", "B07", "C09", "D10") ~ "Sp1",
          cell %in% c("A03", "C03","A08", "C08") ~ "Sp2",
          cell %in% c("B03", "D03", "B08", "D08") ~ "Sp3"
        ))
      
      values$result <- bind_rows(result1, result2) %>% 
        arrange(glass, cell, side)
      
      values$analysis_complete <- TRUE
      output$analysis_status <- renderText("분석이 완료되었습니다!")
      
    }, error = function(e) {
      output$analysis_status <- renderText(paste("오류가 발생했습니다:", e$message))
    })
  })
  
  # 결과 테이블 출력
  output$result_table <- DT::renderDataTable({
    if (is.null(values$result)) {
      return(data.frame(메시지 = "분석을 먼저 실행해주세요."))
    }
    values$result
  }, options = list(pageLength = 15, scrollX = TRUE))
  
  # 메인 그래프
  output$main_plot <- renderPlot({
    if (is.null(values$df1)) return(NULL)
    
    values$df1 %>% 
      mutate(cell = str_sub(`CELL ID`, -3, -1)) %>% 
      mutate(position = str_sub(str_sub(file, -13, -1),1,1)) %>% 
      select(`Glass ID`, no, `Avg Offset`, cell, position) %>% 
      mutate(x = no*10.96) %>% 
      mutate(position = as.numeric(position)) %>% 
      arrange(-position) %>% 
      mutate(side = case_when(
        position == "1" ~ "Left",
        position == "2" ~ "Right",
        position == "3" ~ "Top",
        position == "4" ~ "Down"
      )) %>% 
      mutate(y = `Avg Offset`) %>% 
      ggplot(aes(x, y, col = side)) +
      geom_point() +
      facet_wrap(`Glass ID` ~ cell, nrow = 2) +
      theme_bw() +
      labs(title = "전체 데이터 시각화", x = "X [um]", y = "Avg Offset [um]")
  })
  
  # 프로파일 그래프
  output$profile_plot <- renderPlot({
    if (is.null(values$df1)) return(NULL)
    
    values$df1 %>% 
      mutate(cell = str_sub(`CELL ID`, -3, -1)) %>% 
      mutate(position = str_sub(str_sub(file, -13, -1),1,1)) %>% 
      select(`Glass ID`, no, `Avg Offset`, cell, position) %>% 
      mutate(x = no*10.96) %>% 
      mutate(position = as.numeric(position)) %>% 
      arrange(-position) %>% 
      mutate(side = case_when(
        position == "1" ~ "Left",
        position == "2" ~ "Right",
        position == "3" ~ "Top",
        position == "4" ~ "Down"
      )) %>% 
      mutate(y = `Avg Offset`) %>% 
      group_by(side, x) %>% 
      summarise(y_avg = mean(y, na.rm = TRUE), .groups = "drop") %>% 
      ggplot(aes(x, y_avg - min(y_avg, na.rm = TRUE), col = side)) +
      geom_point() +
      labs(title = "위치별 SIP 잉크젯 Edge Profile",
           x = "x[um]", y = "SIP_height [um]") +
      theme_bw()
  })
  
  # Hump 그래프
  output$hump_plot <- renderPlot({
    if (is.null(values$result)) return(NULL)
    
    values$result %>%
      filter(side != "Down") %>% 
      ggplot(aes(x = side, y = hump_dy, fill = side)) +
      geom_col(position = "dodge") +
      facet_wrap(glass ~ cell, nrow = 2, scales = "free") +
      theme_bw(base_size = 12) +
      labs(title = "Hump Height vs Position of Panel",
           subtitle = "SIP1단",
           x = "side",
           y = "Hump DY [um]") +
      theme(legend.position = "bottom",
            plot.title = element_text(hjust = 0.5, face = "bold"))
  })
  
  # CSV 다운로드
  output$download_csv <- downloadHandler(
    filename = function() {
      paste0("analysis_result_", Sys.Date(), ".csv")
    },
    content = function(file) {
      if (!is.null(values$result)) {
        write.csv(values$result, file, row.names = FALSE)
      }
    }
  )
  
  # 그래프 다운로드
  output$download_plot <- downloadHandler(
    filename = function() {
      paste0("analysis_plot_", Sys.Date(), ".png")
    },
    content = function(file) {
      if (!is.null(values$df1) && !is.null(values$result)) {
        
        p <- values$df1 %>% 
          mutate(cell = str_sub(`CELL ID`, -3, -1)) %>% 
          mutate(position = str_sub(str_sub(file, -13, -1),1,1)) %>% 
          select(`Glass ID`, no, `Avg Offset`, cell, position) %>% 
          mutate(x = no*10.96) %>% 
          mutate(position = as.numeric(position)) %>% 
          arrange(-position) %>% 
          mutate(side = case_when(
            position == "1" ~ "Left",
            position == "2" ~ "Right",
            position == "3" ~ "Top",
            position == "4" ~ "Down"
          )) %>% 
          mutate(y = `Avg Offset`) %>% 
          ggplot(aes(x, y, col = side)) +
          geom_point() +
          facet_wrap(`Glass ID` ~ cell, nrow = 2) +
          theme_bw()
        
        p1 <- values$df1 %>% 
          mutate(cell = str_sub(`CELL ID`, -3, -1)) %>% 
          mutate(position = str_sub(str_sub(file, -13, -1),1,1)) %>% 
          select(`Glass ID`, no, `Avg Offset`, cell, position) %>% 
          mutate(x = no*10.96) %>% 
          mutate(position = as.numeric(position)) %>% 
          arrange(-position) %>% 
          mutate(side = case_when(
            position == "1" ~ "Left",
            position == "2" ~ "Right",
            position == "3" ~ "Top",
            position == "4" ~ "Down"
          )) %>% 
          mutate(y = `Avg Offset`) %>% 
          group_by(side, x) %>% 
          summarise(y_avg = mean(y, na.rm = TRUE), .groups = "drop") %>% 
          ggplot(aes(x, y_avg - min(y_avg, na.rm = TRUE), col = side)) +
          geom_point() +
          labs(title = "위치별 SIP 잉크젯 Edge Profile",
               x = "x[um]", y = "SIP_height [um]") +
          theme_bw()
        
        p2 <- values$result %>%
          filter(side != "Down") %>% 
          ggplot(aes(x = side, y = hump_dy, fill = side)) +
          geom_col(position = "dodge") +
          facet_wrap(glass ~ cell, nrow = 2, scales = "free") +
          theme_bw(base_size = 14) +
          labs(title = "Hump Height vs Position of Panel",
               subtitle = "SIP1단",
               x = "side",
               y = "Hump DY [um]") +
          theme(legend.position = "bottom",
                plot.title = element_text(hjust = 0.5, face = "bold"))
        
        combined_plot <- (p + p1) / p2
        
        ggsave(file, combined_plot, width = 16, height = 12, dpi = 300)
      }
    }
  )
  
  # 다운로드 상태
  output$download_status <- renderText({
    if (values$analysis_complete) {
      "분석이 완료되어 다운로드가 가능합니다."
    } else {
      "분석을 먼저 완료해주세요."
    }
  })
}

# 앱 실행
shinyApp(ui = ui, server = server)