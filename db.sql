-- records all polls, what channel they belong to and metadata
CREATE TABLE IF NOT EXISTS polls (
  id int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  question varchar(100) NOT NULL,
  channelId int(10) UNSIGNED NOT NULL,
  createdAt datetime(6) NOT NULL DEFAULT NOW(),
  createdBy int(10) UNSIGNED NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- records what choices belong to what polls
CREATE TABLE IF NOT EXISTS choices (
  id int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  pollId int(10) UNSIGNED NOT NULL,
  answer varchar(100) NOT NULL,
  pollChoiceId int(10) UNSIGNED NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- records what user choice for specific poll
CREATE TABLE IF NOT EXISTS votes (
  id int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  pollId int(10) UNSIGNED NOT NULL,
  userId int(10) UNSIGNED NOT NULL,
  choiceId int(10) UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UQ_user_vote` (`userId`,`pollId`),
  CONSTRAINT `FK_choices_choiceId` FOREIGN KEY (`choiceId`) REFERENCES `choices` (`id`),
  CONSTRAINT `FK_polls_pollId` FOREIGN KEY (`pollId`) REFERENCES `polls` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

