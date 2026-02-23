package com.yacl;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.yacl")
public class YaclLauncherApplication {

    public static void main(String[] args) {
        SpringApplication.run(YaclLauncherApplication.class, args);
    }
}
