library(readxl)
library(tidyverse)
library(writexl)
library(stringr)
library(gt)
library(showtext) # 한글
library(viridis) #특정 color 묶음
library(patchwork)
showtext_auto()
library(purrr)







getwd()
paths <- c("D:/Non_Documents/!2025/LENS/250630 B3 wsi raw/")
dir_names <- list.dirs(paths,recursive = TRUE)  

library(stringr)
dir_names

file_name <- str_sub(dir_names[5], -11, -8)
setwd(dir_names[2])


df1 <- list.files() |> 
  
  set_names() |>
  map_df(read_csv, .id = "file")


df1 |> mutate(cell = str_sub(`CELL ID`, -3, -1)) |> 
  mutate(position = str_sub(str_sub(file, -13, -1),1,1) ) |> 
  select(`Glass ID`, no, `Avg Offset`, cell,position ) |> 
  mutate(x = no*10.96) |> 
  filter(position !="4") |> 
  
  pivot_wider(names_from = c(`Glass ID`, cell, position), values_from = `Avg Offset`) |> 
  
  mutate(across(c(3:26), ~.x - .x[456])) |> 
  pivot_longer(cols = c(3:26), names_to = c("glass", "cell", "position"),  names_sep = '_', values_to = "y" ) |> arrange(glass, cell, position,no) |> 
  mutate(side = case_when(position =="1" ~ "Left",
                          position =="2" ~ "Right",
                          position =="3" ~ "Top",
                          position =="4" ~ "Down"
  )) |> 
  
    
  group_by(glass, cell, side) |> 
  summarise(hump_dy = round(max(y),1), 
            hump_dx = round(10.96*which.max(y))) |> 
  arrange(glass, cell, side) |> 
  mutate(split = case_when(cell %in% c("A01", "B02", "C04", "D05", "A06", "B07", "C09", "D10")  ~ "Sp1",
                           cell %in% c("A03", "C03","A08", "C08") ~ "Sp2",
                           cell %in% c("B03", "D03", "B08", "D08") ~ "Sp3"  )) -> result1
  


df1 |> mutate(cell = str_sub(`CELL ID`, -3, -1)) |> 
  mutate(position = str_sub(str_sub(file, -13, -1),1,1) ) |> 
  select(`Glass ID`, no, `Avg Offset`, cell,position ) |> 
  mutate(x = no*10.96) |> 
  filter(position =="4") |> 
  rename(glass = `Glass ID`, y= `Avg Offset`) |> 
  mutate(side = case_when(position =="1" ~ "Left",
                          position =="2" ~ "Right",
                          position =="3" ~ "Top",
                          position =="4" ~ "Down"
  )) |> 
  group_by(glass, cell, side) |> 
  summarise(hump_dy = round(max(y)-min(y),1), 
            hump_dx = round(10.96*which.max(y))) |> 
  mutate(split = case_when(cell %in% c("A01", "B02", "C04", "D05", "A06", "B07", "C09", "D10")  ~ "Sp1",
                           cell %in% c("A03", "C03","A08", "C08") ~ "Sp2",
                           cell %in% c("B03", "D03", "B08", "D08") ~ "Sp3"  )) -> result2

bind_rows(result1, result2)  |>   arrange(glass, cell, side) -> result

write.csv(result, paste0(paths, file_name, ".csv"),row.names=F)


p <- 
  df1 |> mutate(cell = str_sub(`CELL ID`, -3, -1)) |> 
    mutate(position = str_sub(str_sub(file, -13, -1),1,1) ) |> 
    select(`Glass ID`, no, `Avg Offset`, cell,position ) |> 
    mutate(x = no*10.96) |> 
    mutate(position = as.numeric(position)) |> 
    
    arrange(- position) |> 
    #filter(position !="4") |> 
    
    # pivot_wider(names_from = c(`Glass ID`, cell, position), values_from = `Avg Offset`) |>
    # 
    # mutate(across(c(3:34), ~.x - .x[456])) |> 
    # pivot_longer(cols = c(3:34), names_to = c("glass", "cell", "position"),  names_sep = '_', values_to = "y" ) |> arrange(glass, cell, position,no) |> 
    mutate(side = case_when(position =="1" ~ "Left",
                            position =="2" ~ "Right",
                            position =="3" ~ "Top",
                            position =="4" ~ "Down"
    )) |> 
    mutate(y=`Avg Offset`) |> 
    

  #filter(side == "Down") |> 
  ggplot(aes(x,y, col=side))+
  geom_point()+
  facet_wrap(`Glass ID`   ~ cell, nrow = 2)+
  theme_bw() 



p1 <- df1 |> 
  mutate(cell = str_sub(`CELL ID`, -3, -1)) |> 
  mutate(position = str_sub(str_sub(file, -13, -1),1,1) ) |> 
  select(`Glass ID`, no, `Avg Offset`, cell,position ) |> 
  mutate(x = no*10.96) |> 
  mutate(position = as.numeric(position)) |> 
  
  arrange(- position) |> 

  mutate(side = case_when(position =="1" ~ "Left",
                          position =="2" ~ "Right",
                          position =="3" ~ "Top",
                          position =="4" ~ "Down"
  )) |> 
  mutate(y=`Avg Offset`) |> 
  group_by(side,x) |> 
  summarise(y_avg = mean(y), .groups = "drop") |> 
  ggplot(aes(x,y_avg-min(y_avg), col=side ))+geom_point()  +
  labs(title = "B3, 상,하,좌,우 위치별 SIP 잉크젯 Edge Profile",
       x = "x[um]", y= "SIP_height [um]")+
  theme_bw()
  

  


p2 <- result |>
  filter(side != "Down") |> 
  ggplot(aes(x = side, y = hump_dy, fill = side)) +
  geom_col(position = "dodge") +
  facet_wrap(glass ~ cell, nrow = 2, scales = "free") +
  theme_bw(base_size = 14) +
  labs(title = "Hump Height vs Position of Panel",
       subtitle = paste0(file_name, "  SIP1단"),
       x = "side",
       y = "Hump DY [um]") +
  theme(legend.position = "bottom",
        plot.title = element_text(hjust = 0.5, face = "bold"))




(p+p1)/p2 

ggsave(paste0(paths, file_name, ".png"))
dev.off()


  

  
